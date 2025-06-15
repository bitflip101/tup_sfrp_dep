# complaints/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone # For resolved_at field

from .models import Complaint, ComplaintUpdate, ComplaintCategory
from .forms import ComplaintForm, ComplaintUpdateForm, ComplaintAdminUpdateForm

# --- User-Facing Views ---

class ComplaintCreateView(LoginRequiredMixin, CreateView):
    """
    Allows a logged-in user to submit a new complaint.
    """
    model = Complaint
    form_class = ComplaintForm
    template_name = 'complaints/complaint_form.html'
    success_url = reverse_lazy('complaints:my_complaints') # Redirect to user's complaints list

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        # Initial status is 'new' by default in model
        response = super().form_valid(form)
        # Trigger notification to admin here (will be handled by signals or direct call to notifications app)
        # from notifications.utils import send_admin_notification
        # send_admin_notification(self.object, 'new_complaint')
        return response

class UserComplaintListView(LoginRequiredMixin, ListView):
    """
    Displays a list of complaints submitted by the current logged-in user.
    """
    model = Complaint
    template_name = 'complaints/user_complaints_list.html'
    context_object_name = 'complaints'
    paginate_by = 10 # Optional: for pagination

    def get_queryset(self):
        # Filter complaints to show only those submitted by the logged-in user
        return Complaint.objects.filter(submitted_by=self.request.user).order_by('-submitted_at')

class UserComplaintDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Displays details of a single complaint submitted by the user.
    Includes public updates.
    """
    model = Complaint
    template_name = 'complaints/user_complaint_detail.html'
    context_object_name = 'complaint'

    def test_func(self):
        # Ensure the user can only view their own complaints
        complaint = self.get_object()
        return complaint.submitted_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['updates'] = self.object.updates.filter(is_public=True).order_by('submitted_at')
        return context

# --- Admin-Facing Views ---

class AdminComplaintListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Displays a list of all complaints for administrators.
    """
    model = Complaint
    template_name = 'complaints/admin_complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 20

    def test_func(self):
        # Only allow staff/admin users to access this view
        # This assumes your custom User model has an is_staff attribute or a user_type for admin
        return self.request.user.is_staff # Or self.request.user.user_type.name == 'Admin'

    def get_queryset(self):
        # Optional: Add filters for status, category, assigned_to
        queryset = Complaint.objects.all().order_by('-submitted_at')
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Complaint.STATUS_CHOICES
        return context


class AdminComplaintDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Displays details of a single complaint for administrators,
    including all updates and forms for admin actions.
    """
    model = Complaint
    template_name = 'complaints/admin_complaint_detail.html'
    context_object_name = 'complaint'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_form'] = ComplaintUpdateForm()
        context['admin_update_form'] = ComplaintAdminUpdateForm(instance=self.object)
        context['updates'] = self.object.updates.all().order_by('submitted_at') # All updates for admin
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'update_message_submit' in request.POST:
            form = ComplaintUpdateForm(request.POST)
            if form.is_valid():
                complaint_update = form.save(commit=False)
                complaint_update.complaint = self.object
                complaint_update.updated_by = request.user
                complaint_update.save()
                # Trigger notification to user if update is public
                # from notifications.utils import send_user_notification
                # if complaint_update.is_public:
                #    send_user_notification(self.object.submitted_by, 'complaint_updated', complaint_update)
                return redirect(self.object.get_admin_detail_url()) # Refresh page
            else:
                # If form is invalid, re-render with errors
                context = self.get_context_data()
                context['update_form'] = form
                return render(request, self.template_name, context)

        elif 'admin_update_submit' in request.POST:
            form = ComplaintAdminUpdateForm(request.POST, instance=self.object)
            if form.is_valid():
                # Check for status change to 'resolved' to set resolved_at
                original_status = self.object.status
                updated_complaint = form.save(commit=False)
                if updated_complaint.status == 'resolved' and original_status != 'resolved':
                    updated_complaint.resolved_at = timezone.now()
                elif updated_complaint.status != 'resolved' and original_status == 'resolved':
                    updated_complaint.resolved_at = None # Clear if status is changed from resolved
                updated_complaint.save()
                # Trigger notifications for status change, assignment change etc.
                # from notifications.utils import send_user_notification, send_admin_notification
                # if updated_complaint.status != original_status:
                #     send_user_notification(self.object.submitted_by, 'complaint_status_changed', self.object)
                return redirect(self.object.get_admin_detail_url())
            else:
                context = self.get_context_data()
                context['admin_update_form'] = form
                return render(request, self.template_name, context)
        return redirect(self.object.get_admin_detail_url()) # Fallback

# Helper method to add to Complaint model for URL
# complaints/models.py
# Add this method to the Complaint model:
# from django.urls import reverse
# ...
# class Complaint(TimeStampModel):
#     # ... existing fields ...
#
#     def get_absolute_url(self):
#         return reverse('complaints:user_complaint_detail', kwargs={'pk': self.pk})
#
#     def get_admin_detail_url(self):
#         return reverse('complaints:admin_complaint_detail', kwargs={'pk': self.pk})
