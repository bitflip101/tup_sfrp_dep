# unified_requests/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse_lazy, reverse # Import reverse for login/register links in errors
from django.contrib import messages
from django.db import transaction
from django.contrib.contenttypes.models import ContentType # Import ContentType

from .forms import UnifiedRequestForm
# Make sure your models are imported correctly
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport
from attachments.models import RequestAttachment # NEW: Import your Attachment model

from notifications.utils import send_complaint_notification_emails # Ensure this utility exists and works
import traceback

class UnifiedRequestSubmitView(View):
    template_name = 'unified_requests/unified_request_form.html'

    def get_context_data(self, **kwargs):
        # Helper to get common context data including login/register URLs
        context = kwargs
        context['login_url'] = reverse_lazy('account_login') # Using django-allauth login URL
        context['register_url'] = reverse_lazy('account_signup') # Using django-allauth signup URL
        return context

    def get(self, request, *args, **kwargs):
        initial_type = request.GET.get('type')
        form = UnifiedRequestForm(initial={'request_type': initial_type}, request=request)
        return render(request, self.template_name, self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form = None
        try:
            form = UnifiedRequestForm(request.POST, request.FILES, request=request)

            if form.is_valid():
                request_type = form.cleaned_data['request_type']
                report_anonymously = form.cleaned_data.get('report_anonymously', False) # Default to False if not present

                # Determine who submitted the request based on authentication and checkbox
                submitted_by_user = None
                anonymous_full_name = None
                anonymous_email = None
                anonymous_phone = None

                if report_anonymously:
                    # If user chose to report anonymously, even if logged in, treat as anonymous for record keeping
                    submitted_by_user = None
                    anonymous_full_name = form.cleaned_data.get('anonymous_full_name')
                    anonymous_email = form.cleaned_data.get('anonymous_email')
                    anonymous_phone = form.cleaned_data.get('anonymous_phone')
                elif request.user.is_authenticated:
                    # User is logged in and did NOT choose to report anonymously
                    submitted_by_user = request.user
                    # No need to populate anonymous fields as user's profile info will be used
                else:
                    # This case should ideally be caught by form.clean() as a non-field error
                    # if an anonymous user tries to submit without checking 'report_anonymously'.
                    # Add a fallback message in case it somehow bypasses form validation.
                    messages.error(request, "You must either log in/register or choose to report anonymously.")
                    return render(request, self.template_name, self.get_context_data(form=form))

                with transaction.atomic():
                    created_object = None 
                    success_message = ""
                    # Determine redirect URL based on anonymous status
                    if submitted_by_user is None: # Submitted anonymously
                        # redirect_url = reverse_lazy('abode:sfrp_lp') # Redirect to landing or a generic thank-you page
                        redirect_url = reverse_lazy('abode:submit_thanks')
                    else: # Submitted by a logged-in user
                        # You might have specific 'my_requests' pages for each type
                        if request_type == 'complaint':
                            redirect_url = reverse_lazy('complaints:my_complaints')
                        # Add other redirects for service, inquiry, emergency if they have user-specific lists
                        else:
                            redirect_url = reverse_lazy('abode:sfrp_lp') # Default for other types if no specific list

                    if request_type == 'complaint':
                        created_object = Complaint.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, # Populated if anonymous, None otherwise
                            email=anonymous_email,       # Populated if anonymous, None otherwise
                            phone_number=anonymous_phone,# Populated if anonymous, None otherwise
                            category=form.cleaned_data['complaint_category'],
                            subject=form.cleaned_data['subject'],
                            description=form.cleaned_data['description'],
                            priority=form.cleaned_data['complaint_priority'],
                            location_address=form.cleaned_data.get('location_address'),
                            latitude=form.cleaned_data.get('latitude'),
                            longitude=form.cleaned_data.get('longitude'),
                            # Attachments need special handling for multiple files, assuming your model supports it
                            # For a single FileField, you'd do: attachment=form.cleaned_data.get('attachments')
                        )
                        # For multiple attachments (FileField with multiple=True)
                        if request.FILES.getlist('attachments'):
                            for f in request.FILES.getlist('attachments'):
                                # Assuming you have an Attachment model linking to Complaint
                                # e.g., ComplaintAttachment.objects.create(complaint=complaint, file=f)
                                pass # Implement your actual file saving logic here

                        success_message = "Your complaint has been submitted successfully."
                        send_complaint_notification_emails(created_object) # Ensure this function is robust

                    elif request_type == 'service':
                        created_object = ServiceRequest.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, email=anonymous_email, phone_number=anonymous_phone, # If your ServiceRequest model has these fields
                            service_type=form.cleaned_data['service_type'],
                            subject=form.cleaned_data['subject'],
                            description=form.cleaned_data['description'],
                            priority=form.cleaned_data.get('priority'),
                            due_date=form.cleaned_data.get('due_date'),
                        )
                        success_message = "Your service request has been submitted successfully."

                    elif request_type == 'inquiry':
                        created_object = Inquiry.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, email=anonymous_email, phone_number=anonymous_phone, # If your Inquiry model has these fields
                            category=form.cleaned_data['inquiry_category'],
                            subject=form.cleaned_data['subject'],
                            question=form.cleaned_data['question'] # Uses the 'question' field
                        )
                        success_message = "Your inquiry has been submitted successfully."

                    elif request_type == 'emergency':
                        created_object = EmergencyReport.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, email=anonymous_email, phone_number=anonymous_phone, # If your EmergencyReport model has these fields
                            emergency_type=form.cleaned_data['emergency_type'],
                            location=form.cleaned_data['location'],
                            description=form.cleaned_data['description']
                        )
                        success_message = "Your emergency report has been submitted. Immediate action will be taken."

                    # NEW: Handle attachments if a request object was created
                    if created_object:
                        files = request.FILES.getlist('attachments')
                        if files:
                            content_type = ContentType.objects.get_for_model(created_object)
                            for f in files:
                                RequestAttachment.objects.create(
                                    content_type=content_type,
                                    object_id=created_object.pk,
                                    file=f,
                                    uploaded_by=request.user if request.user.is_authenticated else None
                                )
                            messages.success(request, success_message + " Your attachment(s) have been uploaded.")
                        else:
                            messages.success(request, success_message)
                    else:
                        messages.error(request, "Failed to create request object.")

                    return redirect(redirect_url)

            else:
                messages.error(request, "Please correct the errors below.")
                return render(request, self.template_name, self.get_context_data(form=form))

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            traceback.print_exc() # Print full traceback to console for debugging
            return render(request, self.template_name, self.get_context_data(form=form if form else UnifiedRequestForm()))