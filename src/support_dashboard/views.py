# support_dashboard/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.urls import reverse, reverse_lazy # Import reverse_lazy for success_url in CBVs
import datetime

# Import Django's generic views
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

# Import the User model
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group # Import Group model
User = get_user_model()

# Import models from request types respective apps
from complaints.models import Complaint, ComplaintCategory
from services.models import ServiceRequest, ServiceType
from inquiries.models import Inquiry, InquiryCategory
from emergencies.models import EmergencyReport, EmergencyType

# Import FAQ models
from faqs.models import FAQCategory, FAQItem

# Import forms (including the new ModelForms, CATEGORY_FORMS map, and User/Group Forms)
from .forms import (
    RequestStatusUpdateForm, RequestAssignmentUpdateForm, RequestFilterForm,
    ComplaintCategoryForm, ServiceTypeForm, InquiryCategoryForm, EmergencyTypeForm, CATEGORY_FORMS,
    UserAdminForm, UserCreateForm, # User forms
    GroupForm, # Group management form
    FAQCategoryForm, FAQItemForm, # Import FAQ forms
)

# Import notification utilities
from notifications.utils import send_request_status_update_email, send_request_assignment_email

# Import STATUS_CHOICES from constants
from unified_requests.constants import STATUS_CHOICES

# --- Mixin for Staff Access & Breadcrumbs ---
class SupportDashboardMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure only logged-in staff members can access the dashboard
    and to provide base breadcrumbs.
    """
    login_url = '/accounts/login/'
    raise_exception = False

    def test_func(self):
        # Allow any authenticated staff member (including superusers)
        # return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "You do not have permission to access the support dashboard.")
        # Redirect to the main dashboard if staff, otherwise home
        if self.request.user.is_staff:
            return redirect('support_dashboard:request_list')
        return redirect('abode:sfrp_lp')
    
    def get_context_data(self, **kwargs):
        # Initialize context. If a superclass (like TemplateView) has get_context_data, call it.
        # Otherwise, start with an empty dictionary.
        context = {}
        if hasattr(super(), 'get_context_data'):
            context = super().get_context_data(**kwargs)

        # Base breadcrumbs for the support dashboard
        if 'breadcrumbs' not in context: # Ensure it's not overwritten if base already set it
            context['breadcrumbs'] = []
        context['breadcrumbs'].append({'name': 'Dashboard', 'url': reverse_lazy('support_dashboard:request_list')})
        return context


# --- Mixin for Admin-level User Management Access ---
class UserAdminRequiredMixin(SupportDashboardMixin):
    """
    Mixin to ensure only superusers can access user management pages.
    You could adjust this to check for specific permissions like 'auth.change_user'
    if you want to delegate user management to non-superuser staff members.
    For now, it strictly checks for is_superuser.
    """
    def test_func(self):
        # Must be authenticated, staff, AND superuser
        return super().test_func() and self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "You need administrator (superuser) privileges to manage users.")
        # Redirect to the support dashboard list for staff members
        return redirect('support_dashboard:request_list')

# --- Mixin for FAQ Management Access & Breadcrumbs ---
class FAQManagementMixin(SupportDashboardMixin):
    """
    Mixin for FAQ management views to provide common breadcrumbs and page titles.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'].append({'name': 'Manage FAQs', 'url': reverse_lazy('support_dashboard:faq_item_list')})
        return context

# --- Unified Request List View with Search and Filtering ---
class RequestListView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_list.html'

    model_map = {
        'complaint': Complaint,
        'service': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    def get(self, request, *args, **kwargs):
        filter_form = RequestFilterForm(request.GET)
        all_requests = self.get_filtered_requests(filter_form)
        all_requests = sorted(all_requests, key=lambda x: x.submitted_at, reverse=True)
        dashboard_stats = self.get_dashboard_statistics()

        context = {
            'requests': all_requests,
            'filter_form': filter_form,
            'dashboard_stats': dashboard_stats
        }
        return render(request, self.template_name, context)

    def get_filtered_requests(self, filter_form):
        combined_objects = []

        for model_name, model_class in self.model_map.items():
            for obj in model_class.objects.all():
                obj.request_type_slug = model_name
                combined_objects.append(obj)

        if filter_form.is_valid():
            cleaned_data = filter_form.cleaned_data

            request_type = cleaned_data.get('request_type')
            if request_type:
                combined_objects = [req for req in combined_objects if req.request_type_slug == request_type]

            q = cleaned_data.get('q')
            if q:
                q_lower = q.lower()
                combined_objects = [
                    req for req in combined_objects
                    if str(req.pk) == q or
                       (hasattr(req, 'subject') and q_lower in req.subject.lower()) or
                       (hasattr(req, 'description') and q_lower in req.description.lower()) or
                       (hasattr(req, 'question') and q_lower in req.question.lower())
                ]

            status = cleaned_data.get('status')
            if status:
                combined_objects = [req for req in combined_objects if hasattr(req, 'status') and req.status == status]

            assigned_to = cleaned_data.get('assigned_to')
            if assigned_to:
                combined_objects = [req for req in combined_objects if hasattr(req, 'assigned_to') and req.assigned_to == assigned_to]

            show_unassigned = cleaned_data.get('show_unassigned')
            if show_unassigned:
                combined_objects = [req for req in combined_objects if hasattr(req, 'assigned_to') and req.assigned_to is None]

            submitted_after = cleaned_data.get('submitted_after')
            submitted_before = cleaned_data.get('submitted_before')

            if submitted_after:
                combined_objects = [req for req in combined_objects if req.submitted_at.date() >= submitted_after]
            if submitted_before:
                combined_objects = [req for req in combined_objects if req.submitted_at.date() <= submitted_before]

        return combined_objects

    def get_dashboard_statistics(self):
        stats = {
            'total_requests': 0,
            'status_counts': {},
            'type_counts': {},
            'new_today': 0,
            'resolved_today': 0,
        }
        today = datetime.date.today()
        for value, display in STATUS_CHOICES:
            if value:
                stats['status_counts'][value] = 0

        for type_slug in self.model_map.keys():
            stats['type_counts'][type_slug] = 0

        for model_name, model_class in self.model_map.items():
            queryset = model_class.objects.all()

            stats['total_requests'] += queryset.count()

            for status_value, _ in STATUS_CHOICES:
                if status_value and hasattr(model_class, 'status'):
                    stats['status_counts'][status_value] += queryset.filter(status=status_value).count()

            stats['type_counts'][model_name] += queryset.count()

            if hasattr(model_class, 'submitted_at'):
                stats['new_today'] += queryset.filter(submitted_at__date=today).count()

            if hasattr(model_class, 'status'):
                stats['resolved_today'] += queryset.filter(status='resolved', submitted_at__date=today).count()

        return stats

# --- RequestDetailView ---
class RequestDetailView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_detail.html'
    model_map = {
        'complaint': Complaint,
        'service': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    def get_object(self, request_type, pk):
        model = self.model_map.get(request_type)
        if not model:
            raise Http404("Invalid request type.")
        return get_object_or_404(model.objects.select_related('submitted_by', 'assigned_to'), pk=pk)

    def get_context_data(self, request_obj, status_form=None, assignment_form=None, **kwargs):
        context = super().get_context_data(**kwargs) # Get base breadcrumbs
        # Add breadcrumbs for Request Detail
        context['breadcrumbs'].append({'name': 'All Requests', 'url': reverse_lazy('support_dashboard:request_list')})
        context['breadcrumbs'].append({'name': f"{request_obj.request_type_slug.replace('_', ' ').title()} #{request_obj.pk}", 'url': reverse_lazy('support_dashboard:request_detail', kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk})})
        
        if status_form is None:
            status_form = RequestStatusUpdateForm(initial={'status': request_obj.status})
        if assignment_form is None:
            assignment_form = RequestAssignmentUpdateForm(initial={'assigned_to': request_obj.assigned_to})

        context.update ({
            'request_obj': request_obj,
            'request_type_display': request_obj.request_type_slug.replace('_', ' ').title(),
            'status_form': status_form,
            'assignment_form': assignment_form,
        })
        return context

    def get(self, request, request_type, pk, *args, **kwargs):
        request_obj = self.get_object(request_type, pk)
        request_obj.request_type_slug = request_type
        
        context = self.get_context_data(request_obj)
        return render(request, self.template_name, context)

    def post(self, request, request_type, pk, *args, **kwargs):
        request_obj = self.get_object(request_type, pk)
        request_obj.request_type_slug = request_type

        status_form = RequestStatusUpdateForm(request.POST)
        assignment_form = RequestAssignmentUpdateForm(request.POST)

        if 'update_status' in request.POST:
            if status_form.is_valid():
                old_status = request_obj.status
                request_obj.status = status_form.cleaned_data['status']
                request_obj.save()
                messages.success(request, f"Status for {request_type.capitalize()} #{request_obj.pk} updated to {request_obj.get_status_display()}.")
                send_request_status_update_email(request_obj, old_status, request_obj.status)
                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update status.")
        elif 'update_assignment' in request.POST:
            if assignment_form.is_valid():
                old_assigned_to = request_obj.assigned_to
                new_assigned_to = assignment_form.cleaned_data['assigned_to']

                if old_assigned_to != new_assigned_to:
                    request_obj.assigned_to = new_assigned_to
                    request_obj.save()
                    assigned_name = request_obj.assigned_to.get_full_name() or request_obj.assigned_to.username if request_obj.assigned_to else "Unassigned"
                    messages.success(request, f"Assignment for {request_type.capitalize()} #{request_obj.pk} updated to {assigned_name}.")
                    if request_obj.assigned_to:
                        send_request_assignment_email(request_obj)
                else:
                    messages.info(request, "Assignment did not change.")

                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update assignment.")
        else:
            messages.error(request, "Invalid form submission.")

        context = self.get_context_data(request_obj, status_form=status_form, assignment_form=assignment_form)
        return render(request, self.template_name, context)

class RequestTrendView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_trend.html'

    model_map = {
        'complaint': Complaint,
        'service': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    def get(self, request, *args, **kwargs):
        filter_form = RequestFilterForm(request.GET)
        return render(request, self.template_name, {})


# --- Category Management Views ---
class CategoryBaseMixin(SupportDashboardMixin):
    """
    Base mixin for category management views to dynamically set model, form, and URLs.
    """
    template_name = 'support_dashboard/category_form.html' # Default form template
    context_object_name = 'category_object' # Generic name for the object in templates

    # Map category type slugs to their actual models and verbose names
    CATEGORY_MODELS = {
        'complaint': {'model': ComplaintCategory, 'verbose': 'Complaint Category', 'plural': 'Complaint Categories'},
        'service': {'model': ServiceType, 'verbose': 'Service Type', 'plural': 'Service Types'},
        'inquiry': {'model': InquiryCategory, 'verbose': 'Inquiry Category', 'plural': 'Inquiry Categories'},
        'emergency': {'model': EmergencyType, 'verbose': 'Emergency Type', 'plural': 'Emergency Types'},
    }

    def dispatch(self, request, *args, **kwargs):
        self.category_type_slug = kwargs.get('category_type_slug')
        
        # Get model info based on the slug from URL
        model_info = self.CATEGORY_MODELS.get(self.category_type_slug)
        if not model_info:
            raise Http404("Invalid category type specified.")
        
        self.model = model_info['model']
        self.verbose_name = model_info['verbose']
        self.verbose_name_plural = model_info['plural']
        self.form_class = CATEGORY_FORMS.get(self.category_type_slug) # Get the correct ModelForm

        # Set the success URL dynamically based on the category type
        self.success_url = reverse_lazy('support_dashboard:category_list', 
                                        kwargs={'category_type_slug': self.category_type_slug})
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_type_slug'] = self.category_type_slug
        context['verbose_name'] = self.verbose_name
        context['verbose_name_plural'] = self.verbose_name_plural

        # Add breadcrumbs for Category Management
        context['breadcrumbs'].append({'name': 'Manage Categories', 'url': reverse_lazy('support_dashboard:category_list', kwargs={'category_type_slug': self.category_type_slug})})

        # Add a title for the page
        if hasattr(self, 'object') and self.object:
                context['page_title'] = f"Edit {self.verbose_name}: {self.object.name}"
                context['breadcrumbs'].append({'name': f"Edit '{self.object.name}'", 'url': self.request.path})
        else: # For CreateView
            context['page_title'] = f"Add New {self.verbose_name}"
            context['breadcrumbs'].append({'name': f"Add New {self.verbose_name}", 'url': self.request.path})
        return context

# View to list all categories of a specific type
class CategoryListView(CategoryBaseMixin, ListView):
    template_name = 'support_dashboard/category_list.html'
    ordering = ['name'] # Default ordering for categories

    def get_queryset(self):
        # The model is already set dynamically by CategoryBaseMixin's dispatch
        return self.model.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.verbose_name_plural
        context['category_models'] = self.CATEGORY_MODELS # For navigation links between categories
        context['breadcrumbs'][-1] = {'name': self.verbose_name_plural, 'url': reverse_lazy('support_dashboard:category_list', kwargs={'category_type_slug': self.category_type_slug})}
        return context

# View to create a new category of a specific type
class CategoryCreateView(CategoryBaseMixin, CreateView):
    template_name = 'support_dashboard/category_form.html' # Use a generic form template

    def form_valid(self, form):
        messages.success(self.request, f"{self.verbose_name} '{form.instance.name}' created successfully.")
        return super().form_valid(form)

# View to update an existing category of a specific type
class CategoryUpdateView(CategoryBaseMixin, UpdateView):
    template_name = 'support_dashboard/category_form.html' # Use a generic form template
    pk_url_kwarg = 'category_pk' # Expected keyword argument in URL for primary key

    def form_valid(self, form):
        messages.success(self.request, f"{self.verbose_name} '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

# View to delete a category of a specific type
class CategoryDeleteView(CategoryBaseMixin, DeleteView):
    template_name = 'support_dashboard/category_confirm_delete.html' # Dedicated delete confirmation template
    pk_url_kwarg = 'category_pk' # Expected keyword argument in URL for primary key

    def form_valid(self, form):
        # When DeleteView's form_valid is called, it means deletion is confirmed.
        # The object is deleted by super().form_valid(form)
        messages.success(self.request, f"{self.verbose_name} '{self.object.name}' deleted successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete {self.verbose_name}"
        # Add specific breadcrumb for delete confirmation
        context['breadcrumbs'].append({'name': f"Delete '{self.object.name}'", 'url': self.request.path})
        return context
    
# --- User Management Views ---
class UserListView(UserAdminRequiredMixin, ListView):
    """
    Lists all user accounts. Requires superuser privileges.
    """
    model = User
    template_name = 'support_dashboard/user_list.html' # Create this template next
    context_object_name = 'users'
    ordering = ['username'] # Order users alphabetically by username

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Manage Users"
        context['breadcrumbs'].append({'name': 'Manage Users', 'url': reverse_lazy('support_dashboard:user_list')})
        return context

class UserCreateView(UserAdminRequiredMixin, CreateView):
    """
    Allows creating new user accounts. Requires superuser privileges.
    """
    model = User
    form_class = UserCreateForm # Use the form that makes password required for new users
    template_name = 'support_dashboard/user_form.html' # Use a generic form template
    success_url = reverse_lazy('support_dashboard:user_list') # Redirect to user list after creation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Add New User"
        context['breadcrumbs'].append({'name': 'Manage Users', 'url': reverse_lazy('support_dashboard:user_list')})
        context['breadcrumbs'].append({'name': 'Add New User', 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"User '{form.instance.username}' created successfully.")
        return super().form_valid(form)

class UserUpdateView(UserAdminRequiredMixin, UpdateView):
    """
    Allows updating existing user accounts. Requires superuser privileges.
    """
    model = User
    form_class = UserAdminForm # Use the form where password is optional for updates
    template_name = 'support_dashboard/user_form.html' # Reuses generic form template
    pk_url_kwarg = 'user_pk' # Expected keyword argument in URL for user primary key
    context_object_name = 'user_obj' # Name for the user object in the template
    success_url = reverse_lazy('support_dashboard:user_list') # Redirect to user list after update

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit User: {self.object.username}"
        context['breadcrumbs'].append({'name': 'Manage Users', 'url': reverse_lazy('support_dashboard:user_list')})
        context['breadcrumbs'].append({'name': f"Edit '{self.object.username}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"User '{form.instance.username}' updated successfully.")
        return super().form_valid(form)

class UserDeleteView(UserAdminRequiredMixin, DeleteView):
    """
    Allows deleting user accounts. Requires superuser privileges.
    Prevents deletion of self.
    """
    model = User
    template_name = 'support_dashboard/user_confirm_delete.html' # Create this template next
    pk_url_kwarg = 'user_pk'
    context_object_name = 'user_obj'
    success_url = reverse_lazy('support_dashboard:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete User: {self.object.username}"
        context['breadcrumbs'].append({'name': 'Manage Users', 'url': reverse_lazy('support_dashboard:user_list')})
        context['breadcrumbs'].append({'name': f"Delete '{self.object.username}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        # Prevent a superuser from deleting their own account via this interface
        if self.request.user.pk == self.object.pk:
            messages.error(self.request, "You cannot delete your own user account through this interface.")
            return redirect(self.get_success_url())
        
        messages.success(self.request, f"User '{self.object.username}' deleted successfully.")
        return super().form_valid(form)

# --- Group Management Views (with Breadcrumbs) ---
class GroupListView(UserAdminRequiredMixin, ListView):
    """
    Lists all user groups. Requires superuser privileges.
    """
    model = Group
    template_name = 'support_dashboard/group_list.html' # Create this template next
    context_object_name = 'groups'
    ordering = ['name'] # Order groups alphabetically by name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Manage Groups"
        context['breadcrumbs'].append({'name': 'Manage Groups', 'url': reverse_lazy('support_dashboard:group_list')})
        return context

class GroupCreateView(UserAdminRequiredMixin, CreateView):
    """
    Allows creating new user groups. Requires superuser privileges.
    """
    model = Group
    form_class = GroupForm # Use the new GroupForm
    template_name = 'support_dashboard/group_form.html' # Use a generic form template
    success_url = reverse_lazy('support_dashboard:group_list') # Redirect to group list after creation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Add New Group"
        context['breadcrumbs'].append({'name': 'Manage Groups', 'url': reverse_lazy('support_dashboard:group_list')})
        context['breadcrumbs'].append({'name': 'Add New Group', 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Group '{form.instance.name}' created successfully.")
        return super().form_valid(form)

class GroupUpdateView(UserAdminRequiredMixin, UpdateView):
    """
    Allows updating existing user groups. Requires superuser privileges.
    """
    model = Group
    form_class = GroupForm # Use the new GroupForm
    template_name = 'support_dashboard/group_form.html' # Reuses generic form template
    pk_url_kwarg = 'group_pk' # Expected keyword argument in URL for group primary key
    context_object_name = 'group_obj' # Name for the group object in the template
    success_url = reverse_lazy('support_dashboard:group_list') # Redirect to group list after update

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit Group: {self.object.name}"
        context['breadcrumbs'].append({'name': 'Manage Groups', 'url': reverse_lazy('support_dashboard:group_list')})
        context['breadcrumbs'].append({'name': f"Edit '{self.object.name}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Group '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

class GroupDeleteView(UserAdminRequiredMixin, DeleteView):
    """
    Allows deleting user groups. Requires superuser privileges.
    """
    model = Group
    template_name = 'support_dashboard/group_confirm_delete.html' # Create this template next
    pk_url_kwarg = 'group_pk'
    context_object_name = 'group_obj'
    success_url = reverse_lazy('support_dashboard:group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete Group: {self.object.name}"
        context['breadcrumbs'].append({'name': 'Manage Groups', 'url': reverse_lazy('support_dashboard:group_list')})
        context['breadcrumbs'].append({'name': f"Delete '{self.object.name}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Group '{self.object.name}' deleted successfully.")
        return super().form_valid(form)
    
# --- FAQ Management Views ---
class FAQCategoryListView(FAQManagementMixin, ListView):
    """
    Lists all FAQ categories for management.
    """
    model = FAQCategory
    template_name = 'support_dashboard/faqs/category_list.html'
    context_object_name = 'categories'
    ordering = ['order', 'name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Manage FAQ Categories"
        # The 'Manage FAQs' breadcrumb is handled by FAQManagementMixin
        context['breadcrumbs'].append({'name': 'Categories List', 'url': reverse_lazy('support_dashboard:faq_category_list')})
        return context

class FAQCategoryCreateView(FAQManagementMixin, CreateView):
    """
    Allows creating new FAQ categories.
    """
    model = FAQCategory
    form_class = FAQCategoryForm
    template_name = 'support_dashboard/faqs/faq_form.html' # Generic form template
    success_url = reverse_lazy('support_dashboard:faq_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Add New FAQ Category"
        context['form_title'] = "Add New FAQ Category"
        context['breadcrumbs'].append({'name': 'Add New Category', 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Category '{form.instance.name}' created successfully.")
        return super().form_valid(form)

class FAQCategoryUpdateView(FAQManagementMixin, UpdateView):
    """
    Allows updating existing FAQ categories.
    """
    model = FAQCategory
    form_class = FAQCategoryForm
    template_name = 'support_dashboard/faqs/faq_form.html' # Generic form template
    context_object_name = 'obj' # Generic object name for the form template
    success_url = reverse_lazy('support_dashboard:faq_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit FAQ Category: {self.object.name}"
        context['form_title'] = f"Edit FAQ Category: {self.object.name}"
        context['breadcrumbs'].append({'name': f"Edit '{self.object.name}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Category '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

class FAQCategoryDeleteView(FAQManagementMixin, DeleteView):
    """
    Allows deleting FAQ categories.
    """
    model = FAQCategory
    template_name = 'support_dashboard/faqs/faq_confirm_delete.html' # Generic delete confirmation template
    context_object_name = 'obj' # Generic object name for the delete template
    success_url = reverse_lazy('support_dashboard:faq_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete FAQ Category: {self.object.name}"
        context['delete_message'] = f"Are you sure you want to delete the FAQ category '{self.object.name}'? All associated FAQ items will also be deleted."
        context['breadcrumbs'].append({'name': f"Delete '{self.object.name}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Category '{self.object.name}' and its items deleted successfully.")
        return super().form_valid(form)


class FAQItemListView(FAQManagementMixin, ListView):
    """
    Lists all FAQ items for management, with optional filtering by category.
    """
    model = FAQItem
    template_name = 'support_dashboard/faqs/item_list.html'
    context_object_name = 'items'
    ordering = ['category__order', 'order', 'question']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Manage FAQ Items"
        context['categories'] = FAQCategory.objects.all().order_by('order', 'name') # For the filter dropdown
        context['selected_category_id'] = self.request.GET.get('category')
        if context['selected_category_id']:
            try:
                context['selected_category_name'] = FAQCategory.objects.get(id=context['selected_category_id']).name
            except FAQCategory.DoesNotExist:
                context['selected_category_name'] = None
        
        context['breadcrumbs'].append({'name': 'Items List', 'url': reverse_lazy('support_dashboard:faq_item_list')})
        return context

class FAQItemCreateView(FAQManagementMixin, CreateView):
    """
    Allows creating new FAQ items.
    """
    model = FAQItem
    form_class = FAQItemForm
    template_name = 'support_dashboard/faqs/faq_form.html' # Generic form template
    success_url = reverse_lazy('support_dashboard:faq_item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Add New FAQ Item"
        context['form_title'] = "Add New FAQ Item"
        context['breadcrumbs'].append({'name': 'Add New Item', 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Item '{form.instance.question}' created successfully.")
        return super().form_valid(form)

class FAQItemUpdateView(FAQManagementMixin, UpdateView):
    """
    Allows updating existing FAQ items.
    """
    model = FAQItem
    form_class = FAQItemForm
    template_name = 'support_dashboard/faqs/faq_form.html' # Generic form template
    context_object_name = 'obj' # Generic object name for the form template
    success_url = reverse_lazy('support_dashboard:faq_item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit FAQ Item: {self.object.question}"
        context['form_title'] = f"Edit FAQ Item: {self.object.question}"
        context['breadcrumbs'].append({'name': f"Edit '{self.object.question}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Item '{form.instance.question}' updated successfully.")
        return super().form_valid(form)

class FAQItemDeleteView(FAQManagementMixin, DeleteView):
    """
    Allows deleting FAQ items.
    """
    model = FAQItem
    template_name = 'support_dashboard/faqs/faq_confirm_delete.html' # Generic delete confirmation template
    context_object_name = 'obj' # Generic object name for the delete template
    success_url = reverse_lazy('support_dashboard:faq_item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete FAQ Item: {self.object.question}"
        context['delete_message'] = f"Are you sure you want to delete the FAQ item: '{self.object.question}'?"
        context['breadcrumbs'].append({'name': f"Delete '{self.object.question}'", 'url': self.request.path})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"FAQ Item '{self.object.question}' deleted successfully.")
        return super().form_valid(form)