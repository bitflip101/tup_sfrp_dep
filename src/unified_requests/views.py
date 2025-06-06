# unified_requests/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction

from .forms import UnifiedRequestForm
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

from notifications.utils import send_complaint_notification_emails

class UnifiedRequestSubmitView(LoginRequiredMixin, View):
    """
    Handles the submission of a unified request (Complaint, Service, Inquiry, Emergency).
    """
    template_name = 'unified_requests/unified_request_form.html'

    def get(self, request, *args, **kwargs):
        initial_type = request.GET.get('type') # Get type from URL parameter
        form = UnifiedRequestForm(initial={'request_type': initial_type})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UnifiedRequestForm(request.POST)

        if form.is_valid():
            request_type = form.cleaned_data['request_type']
            submitted_by = request.user

            try:
                with transaction.atomic(): # Ensure atomicity for database operations
                    if request_type == 'complaint':
                        complaint = Complaint.objects.create(
                            submitted_by=submitted_by,
                            category=form.cleaned_data['complaint_category'],
                            subject=form.cleaned_data['subject'],
                            description=form.cleaned_data['description'],
                            priority=form.cleaned_data['complaint_priority']
                        )
                        success_message = "Your complaint has been submitted successfully."
                        print("COMPLAINTS_BEFORE EMAIL_SENDING.")
                        send_complaint_notification_emails(complaint)
                        print("COMPLAINTS_AFTER EMAIL_SENDING.")
                        redirect_url = reverse_lazy('complaints:my_complaints')

                    elif request_type == 'service':
                        service_request = ServiceRequest.objects.create(
                            submitted_by=submitted_by,
                            service_type=form.cleaned_data['service_type'],
                            subject=form.cleaned_data['subject'],
                            description=form.cleaned_data['description']
                        )
                        success_message = "Your service request has been submitted successfully."
                        # You'll need a 'my_service_requests' view/URL later
                        # Future: send_service_request_notification_emails(service_request)
                        redirect_url = reverse_lazy('abode:sfrp_lp') # Placeholder

                    elif request_type == 'inquiry':
                        inquiry = Inquiry.objects.create(
                            submitted_by=submitted_by,
                            category=form.cleaned_data['inquiry_category'],
                            subject=form.cleaned_data['subject'],
                            question=form.cleaned_data['question'] # Or description, depending on model choice
                        )
                        success_message = "Your inquiry has been submitted successfully."
                        # Future: send_inquiry_notification_emails(inquiry)
                        # You'll need a 'my_inquiries' view/URL later
                        redirect_url = reverse_lazy('home:landing_page') # Placeholder

                    elif request_type == 'emergency':
                        emergency_report = EmergencyReport.objects.create(
                            submitted_by=submitted_by,
                            emergency_type=form.cleaned_data['emergency_type'],
                            location=form.cleaned_data['location'],
                            description=form.cleaned_data['description']
                        )
                        success_message = "Your emergency report has been submitted. Immediate action will be taken."
                        # Future: send_emergency_notification_emails(emergency_report)
                        # You'll need a 'my_emergency_reports' view/URL later
                        redirect_url = reverse_lazy('home:landing_page') # Placeholder

                    messages.success(request, success_message)
                    # Trigger notifications for admin here
                    # from apps.notifications.utils import send_admin_notification
                    # send_admin_notification(self.object, f'{request_type}_submitted')
                    return redirect(redirect_url)

            except Exception as e:
                messages.error(request, f"An error occurred during submission: {e}")
                # Log the error
                return render(request, self.template_name, {'form': form})

        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, self.template_name, {'form': form})

