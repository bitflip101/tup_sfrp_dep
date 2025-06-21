# support_dashboard/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q # For searching across multiple fields/models
from django.http import Http404 # NEW: For raising 404 in get_object
from django.urls import reverse # NEW: Ensure reverse is imported if used in view logic
import datetime # NEW: For date filtering operations

# Import your models from their respective apps
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

# Import your forms
from .forms import RequestStatusUpdateForm, RequestAssignmentUpdateForm
from .forms import RequestFilterForm # Import the RequestFilterForm

# Import notification utilities
from notifications.utils import send_request_status_update_email, send_request_assignment_email

# Import STATUS_CHOICES from constants (used for dynamic status counts)
from unified_requests.constants import STATUS_CHOICES # STATUS_CHOICES is defined unified_requests

# NotificationContextMixin
class SupportDashboardMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure only logged-in staff members can access the dashboard.
    """
    login_url = '/accounts/login/' # Redirect to login if not authenticated
    raise_exception = False # Don't raise 403, just redirect to login

    def test_func(self):
        # Only allow users marked as staff or superuser
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "You do not have permission to access the support dashboard.")
        return redirect('abode:sfrp_lp') # Redirect to a home page for now, then create another suitable page.

# Unified Request List View with Search and Filtering
class RequestListView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_list.html'

    # A map to easily get model class by its slug
    model_map = {
        'complaint': Complaint,
        'service': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    def get(self, request, *args, **kwargs):
        # 1. Instantiate the filter form with GET parameters
        filter_form = RequestFilterForm(request.GET)
        
        # 2. Get the filtered and sorted requests
        all_requests = self.get_filtered_requests(filter_form)
        
        # Sort requests by creation date, newest first (common dashboard requirement)
        all_requests = sorted(all_requests, key=lambda x: x.submitted_at, reverse=True)

        # Fetch Dashboad Statistics
        dashboard_stats = self.get_dashboard_statistics()

        context = {
            'requests': all_requests,
            'filter_form': filter_form, # Pass the filter form to the template
            'dashboard_stats': dashboard_stats # Pass statistics to the template
        }
        return render(request, self.template_name, context)

    def get_filtered_requests(self, filter_form):
        """
        Gathers requests from all models, attaches type slugs, and applies filters
        based on the provided form.
        """
        combined_objects = []

        # Step 1: Gather all objects and attach request_type_slug
        # Using select_related for common related fields to minimize queries in iteration
        for model_name, model_class in self.model_map.items():
            # Adjust select_related based on common fields across all models
            # or fetch specific fields per model if they differ greatly.
            # For simplicity, fetching all, then adding type slug.
            # If you have specific fields to prefetch for each model, do it here
            # e.g., if model_name == 'complaint': qs = Complaint.objects.select_related('category')
            for obj in model_class.objects.all():
                obj.request_type_slug = model_name # Attach the slug for consistent access
                combined_objects.append(obj)

        # Step 2: Apply filters if the form is valid
        if filter_form.is_valid():
            cleaned_data = filter_form.cleaned_data

            # Filter by Request Type
            request_type = cleaned_data.get('request_type')
            if request_type:
                combined_objects = [req for req in combined_objects if req.request_type_slug == request_type]

            # Search by 'q' (ID, Subject, Description, Question for Inquiry)
            q = cleaned_data.get('q')
            if q:
                q_lower = q.lower()
                combined_objects = [
                    req for req in combined_objects
                    if str(req.pk) == q or # Match by ID (exact string match)
                       (hasattr(req, 'subject') and q_lower in req.subject.lower()) or # For Complaint, Service, Emergency
                       (hasattr(req, 'description') and q_lower in req.description.lower()) or # For Complaint, Service, Emergency
                       (hasattr(req, 'question') and q_lower in req.question.lower()) # For Inquiry
                ]

            # Filter by Status
            status = cleaned_data.get('status')
            if status:
                combined_objects = [req for req in combined_objects if hasattr(req, 'status') and req.status == status]

            # Filter by Assigned Agent
            assigned_to = cleaned_data.get('assigned_to') # This will be a User object or None
            if assigned_to:
                combined_objects = [req for req in combined_objects if hasattr(req, 'assigned_to') and req.assigned_to == assigned_to]
            
            # Filter by Unassigned Only (applied after assigned_to to allow specific agent AND unassigned)
            show_unassigned = cleaned_data.get('show_unassigned')
            if show_unassigned:
                combined_objects = [req for req in combined_objects if hasattr(req, 'assigned_to') and req.assigned_to is None]

            # Filter by Submission Date Range
            submitted_after = cleaned_data.get('submitted_after')
            submitted_before = cleaned_data.get('submitted_before')

            if submitted_after:
                combined_objects = [req for req in combined_objects if req.submitted_at.date() >= submitted_after]
            if submitted_before:
                combined_objects = [req for req in combined_objects if req.submitted_at.date() <= submitted_before]

        return combined_objects

    # Method to fetch dashboard statistics
    def get_dashboard_statistics(self):
        stats = {
            'total_requests': 0,
            'status_counts': {}, # e.g., {'new': 10, 'in_progress': 5}
            'type_counts': {},   # e.g., {'complaint': 7, 'service': 8}
            'new_today': 0,
            'resolved_today': 0,
            # Option to add more as needed, e.g., 'new_this_week', 'resolved_this_week'
        }
        today = datetime.date.today()
        # Initialize status counts for all possible statuses
        for value, display in STATUS_CHOICES:
            if value: # Exclude the 'All Statuses' empty choice
                stats['status_counts'][value] = 0

        # Initialize type counts for all possible types (from form's choices or model_map keys)
        for type_slug in self.model_map.keys():
            stats['type_counts'][type_slug] = 0
        
        # Iterate through each model to collect statistics
        for model_name, model_class in self.model_map.items():
            # Get the queryset for the current model
            queryset = model_class.objects.all()

            # Total requests
            stats['total_requests'] += queryset.count()

            # Requests by Status
            for status_value, _ in STATUS_CHOICES:
                if status_value and hasattr(model_class, 'status'): # Check if model has a 'status' field
                    stats['status_counts'][status_value] += queryset.filter(status=status_value).count()

            # Requests by Type (already grouped by iterating model_map)
            stats['type_counts'][model_name] += queryset.count()

            # New Requests Today (assuming the field exists, submitted_at)
            if hasattr(model_class, 'submitted_at'):
                stats['new_today'] += queryset.filter(submitted_at__date=today).count()

            # Resolved Requests Today (assuming 'status' and 'resolved' status exist)
            if hasattr(model_class, 'status'):
                stats['resolved_today'] += queryset.filter(status='resolved', submitted_at__date=today).count() # Or updated_at__date=today if resolution date is tracked separately

        return stats

# RequestDetailView (Your existing RequestDetailView, slightly adjusted for consistency)
class RequestDetailView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_detail.html'
    model_map = { # Added model_map for consistency with RequestListView
        'complaint': Complaint,
        'service': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    def get_object(self, request_type, pk):
        model = self.model_map.get(request_type)
        if not model:
            raise Http404("Invalid request type.")
        # Pre-fetch related objects for detail view and email notifications
        return get_object_or_404(model.objects.select_related('submitted_by', 'assigned_to'), pk=pk)

    def get_context_data(self, request_obj, status_form=None, assignment_form=None):
        # Initialize forms if not provided (e.g., in a GET request)
        if status_form is None:
            status_form = RequestStatusUpdateForm(initial={'status': request_obj.status})
        if assignment_form is None:
            assignment_form = RequestAssignmentUpdateForm(initial={'assigned_to': request_obj.assigned_to})

        return {
            'request_obj': request_obj,
            'request_type_display': request_obj.request_type_slug.replace('_', ' ').title(), # Use slug for display
            'status_form': status_form,
            'assignment_form': assignment_form,
        }

    def get(self, request, request_type, pk, *args, **kwargs):
        request_obj = self.get_object(request_type, pk)
        request_obj.request_type_slug = request_type # Attach slug for consistent access
        
        context = self.get_context_data(request_obj)
        return render(request, self.template_name, context)

    def post(self, request, request_type, pk, *args, **kwargs):
        request_obj = self.get_object(request_type, pk) # Use the helper method
        request_obj.request_type_slug = request_type # Attach slug for consistent access

        # Initialize forms for potential re-rendering with errors
        status_form = RequestStatusUpdateForm(request.POST)
        assignment_form = RequestAssignmentUpdateForm(request.POST)

        if 'update_status' in request.POST:
            if status_form.is_valid():
                old_status = request_obj.status # Capture old status before updating
                request_obj.status = status_form.cleaned_data['status']
                request_obj.save()
                messages.success(request, f"Status for {request_type.capitalize()} #{request_obj.pk} updated to {request_obj.get_status_display()}.")

                send_request_status_update_email(request_obj, old_status, request_obj.status)
                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update status.")
        elif 'update_assignment' in request.POST:
            if assignment_form.is_valid():
                old_assigned_to = request_obj.assigned_to # Capture old assignment
                new_assigned_to = assignment_form.cleaned_data['assigned_to']

                # Only send email if assignment actually changed
                if old_assigned_to != new_assigned_to:
                    request_obj.assigned_to = new_assigned_to
                    request_obj.save()
                    assigned_name = request_obj.assigned_to.get_full_name() or request_obj.assigned_to.username if request_obj.assigned_to else "Unassigned"
                    messages.success(request, f"Assignment for {request_type.capitalize()} #{request_obj.pk} updated to {assigned_name}.")

                    if request_obj.assigned_to: # Only send if assigned to someone
                        send_request_assignment_email(request_obj)
                else:
                    messages.info(request, "Assignment did not change.") # Inform user if no change

                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update assignment.")
        else:
            messages.error(request, "Invalid form submission.")

        # Re-render with errors if forms were invalid or invalid action
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
        # 1. Instantiate the filter form with GET parameters
        filter_form = RequestFilterForm(request.GET)
        
        # 2. Get the filtered and sorted requests
        # all_requests = self.get_filtered_requests(filter_form)
        
        # Sort requests by creation date, newest first (common dashboard requirement)
        # all_requests = sorted(all_requests, key=lambda x: x.submitted_at, reverse=True)

        # Fetch Dashboad Statistics
        # dashboard_stats = self.get_dashboard_statistics()

        # context = {
        #     'requests': all_requests,
        #     'filter_form': filter_form, # Pass the filter form to the template
        #     'dashboard_stats': dashboard_stats # Pass statistics to the template
        # }

        return render(request, self.template_name, {})


