# support_dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q # For searching across multiple fields/models

# Import your models from their respective apps
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

from .forms import RequestStatusUpdateForm, RequestAssignmentUpdateForm # NEW: Import our custom forms
from notifications.utils import send_request_status_update_email, send_request_assignment_email

class SupportDashboardMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure only logged-in staff members can access the dashboard.
    Customize test_func as needed (e.g., check if user.is_staff or has specific permissions).
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
        return redirect('abode:sfrp_lp') # Redirect to a home page or another suitable page

class RequestListView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/requests_list.html'

    def get(self, request, *args, **kwargs):
        # Fetch all types of requests
        complaints = Complaint.objects.all().select_related('submitted_by', 'category', 'assigned_to')
        service_requests = ServiceRequest.objects.all().select_related('submitted_by', 'service_type', 'assigned_to')
        inquiries = Inquiry.objects.all().select_related('submitted_by', 'category', 'assigned_to')
        emergency_reports = EmergencyReport.objects.all().select_related('submitted_by', 'emergency_type', 'assigned_to')

        # Combine them into a single list (can be ordered by submitted_at for all)
        all_requests = sorted(
            list(complaints) + list(service_requests) + list(inquiries) + list(emergency_reports),
            key=lambda x: x.submitted_at,
            reverse=True
        )
        # NEW: Add a 'request_type_slug' attribute to each object for use in templates
        for req in all_requests:
            if isinstance(req, Complaint):
                req.request_type_slug = 'complaint'
            elif isinstance(req, ServiceRequest):
                req.request_type_slug = 'service'
            elif isinstance(req, Inquiry):
                req.request_type_slug = 'inquiry'
            elif isinstance(req, EmergencyReport):
                req.request_type_slug = 'emergency'
            else:
                req.request_type_slug = 'unknown' # Fallback

        context = {
            'requests': all_requests,
        }
        return render(request, self.template_name, context)

class RequestDetailView(SupportDashboardMixin, View):
    template_name = 'support_dashboard/request_detail.html'

    def get(self, request, request_type, pk, *args, **kwargs):
        request_obj = None
        if request_type == 'complaint':
            request_obj = get_object_or_404(Complaint.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'service':
            request_obj = get_object_or_404(ServiceRequest.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'inquiry':
            request_obj = get_object_or_404(Inquiry.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'emergency':
            request_obj = get_object_or_404(EmergencyReport.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        else:
            messages.error(request, "Invalid request type.")
            return redirect('support_dashboard:request_list')

        # Add request_type_slug for consistency in URLs
        # This is important for the notification URLs to work
        if isinstance(request_obj, Complaint):
            request_obj.request_type_slug = 'complaint'
        elif isinstance(request_obj, ServiceRequest):
            request_obj.request_type_slug = 'service'
        elif isinstance(request_obj, Inquiry):
            request_obj.request_type_slug = 'inquiry'
        elif isinstance(request_obj, EmergencyReport):
            request_obj.request_type_slug = 'emergency'

        status_form = RequestStatusUpdateForm(initial={'status': request_obj.status})
        assignment_form = RequestAssignmentUpdateForm(initial={'assigned_to': request_obj.assigned_to})

        context = {
            'request_obj': request_obj,
            'request_type': request_type,
            'status_form': status_form,
            'assignment_form': assignment_form,
        }
        return render(request, self.template_name, context)

    def post(self, request, request_type, pk, *args, **kwargs):
        request_obj = None
        # Use select_related to prefetch submitted_by and assigned_to for email sending later
        if request_type == 'complaint':
            request_obj = get_object_or_404(Complaint.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'service':
            request_obj = get_object_or_404(ServiceRequest.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'inquiry':
            request_obj = get_object_or_404(Inquiry.objects.select_related('submitted_by', 'assigned_to'), pk=pk)
        elif request_type == 'emergency':
            request_obj = get_object_or_404(EmergencyReport.objects.select_related('submitted_by', 'assigned_to'), pk=pk)

        if request_obj is None:
            messages.error(request, "Invalid request type or ID.")
            return redirect('support_dashboard:request_list')

        # Add request_type_slug to the object *before* sending emails if it's not a model property
        # This is critical for reverse() to work in email utility functions
        if isinstance(request_obj, Complaint):
            request_obj.request_type_slug = 'complaint'
        elif isinstance(request_obj, ServiceRequest):
            request_obj.request_type_slug = 'service'
        elif isinstance(request_obj, Inquiry):
            request_obj.request_type_slug = 'inquiry'
        elif isinstance(request_obj, EmergencyReport):
            request_obj.request_type_slug = 'emergency'


        if 'update_status' in request.POST:
            status_form = RequestStatusUpdateForm(request.POST)
            if status_form.is_valid():
                old_status = request_obj.status # Capture old status before updating
                request_obj.status = status_form.cleaned_data['status']
                request_obj.save()
                messages.success(request, f"Status for {request_type.capitalize()} #{request_obj.pk} updated to {request_obj.get_status_display()}.")

                # Send email notification to user about status change
                send_request_status_update_email(request_obj, old_status, request_obj.status)

                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update status.")
        elif 'update_assignment' in request.POST:
            assignment_form = RequestAssignmentUpdateForm(request.POST)
            if assignment_form.is_valid():
                old_assigned_to = request_obj.assigned_to # Capture old assignment
                new_assigned_to = assignment_form.cleaned_data['assigned_to']

                # Only send email if assignment actually changed
                if old_assigned_to != new_assigned_to:
                    request_obj.assigned_to = new_assigned_to
                    request_obj.save()
                    assigned_name = request_obj.assigned_to.get_full_name() or request_obj.assigned_to.username if request_obj.assigned_to else "Unassigned"
                    messages.success(request, f"Assignment for {request_type.capitalize()} #{request_obj.pk} updated to {assigned_name}.")

                    # Send email notification to the new assigned person (if any)
                    if request_obj.assigned_to:
                        send_request_assignment_email(request_obj)
                else:
                    messages.info(request, "Assignment did not change.")


                return redirect('support_dashboard:request_detail', request_type=request_type, pk=pk)
            else:
                messages.error(request, "Failed to update assignment.")
        else:
            messages.error(request, "Invalid form submission.")

        # If forms are invalid or no specific action, re-render with errors
        status_form = RequestStatusUpdateForm(initial={'status': request_obj.status})
        assignment_form = RequestAssignmentUpdateForm(initial={'assigned_to': request_obj.assigned_to})
        context = {
            'request_obj': request_obj,
            'request_type': request_type,
            'status_form': status_form,
            'assignment_form': assignment_form,
        }
        return render(request, self.template_name, context)