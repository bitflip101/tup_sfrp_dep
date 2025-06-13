# unified_requests/views.py
from django.shortcuts import render, redirect, get_list_or_404
from django.views.generic import View, TemplateView 
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy # Important for reverse_lazy
import traceback # For debugging

# Your models
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

# Your forms
from .forms import UnifiedRequestForm

# Your notification utility functions
from notifications.utils import send_new_request_submission_notifications # Updated import!

# For attachments (if you have a RequestAttachment model)
from django.contrib.contenttypes.models import ContentType
from attachments.models import RequestAttachment

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
                    # redirect_url = reverse_lazy('abode:submit_thanks')
                    # The redirect_url will now ALWAYS go to the success page
                    # The success page itself will handle showing user-specific links if logged in
                    redirect_url_args = {'pk':None, 'request_type': request_type} # Prepare args for redirect

                    # --- Request Object Creation ---
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
                        )
                        success_message = "Your complaint has been submitted successfully."
                        # For logged-in users, redirect to their list of complaints if it exists
                        if submitted_by_user:
                             redirect_url = reverse_lazy('complaints:my_complaints') # Assuming this URL exists

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
                        # For logged-in users, redirect to their list of complaints if it exists
                        if submitted_by_user:
                             redirect_url = reverse_lazy('abode:submit_thankss') # Assuming this URL exists

                    elif request_type == 'inquiry':
                        created_object = Inquiry.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, email=anonymous_email, phone_number=anonymous_phone, # If your Inquiry model has these fields
                            category=form.cleaned_data['inquiry_category'],
                            subject=form.cleaned_data['subject'],
                            question=form.cleaned_data['question'] # Uses the 'question' field
                        )
                        success_message = "Your inquiry has been submitted successfully."
                        # For logged-in users, redirect to their list of complaints if it exists
                        if submitted_by_user:
                             redirect_url = reverse_lazy('abode:submit_thankss') # Assuming this URL exists

                    elif request_type == 'emergency':
                        created_object = EmergencyReport.objects.create(
                            submitted_by=submitted_by_user,
                            full_name=anonymous_full_name, email=anonymous_email, phone_number=anonymous_phone, # If your EmergencyReport model has these fields
                            emergency_type=form.cleaned_data['emergency_type'],
                            location=form.cleaned_data['location'],
                            description=form.cleaned_data['description']
                        )
                        success_message = "Your emergency report has been submitted. Immediate action will be taken."
                        # For logged-in users, redirect to their list of complaints if it exists
                        if submitted_by_user:
                             redirect_url = reverse_lazy('abode:submit_thankss') # Assuming this URL exists

                    # --- Common Post-Creation Logic ---
                    if created_object:
                        # Set request_type_slug explicitly on the created object for the notification utility
                        # This is crucial for building the correct URLs in the emails
                        created_object.request_type_slug = request_type
                        
                        # Handle attachments
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

                        # NEW: Call the generic notification function for initial submission
                        send_new_request_submission_notifications(created_object)

                        # Update redirect args with actual PK
                        redirect_url_args['pk'] = created_object.pk

                        # Redirect to the new generic success page
                        return redirect('unified_requests:success_page', **redirect_url_args)
                    else:
                        messages.error(request, "Failed to create request object.")
                        return redirect(request, self.template_name, self.get_context_data(form=form))

            else: # Form is not valid
                messages.error(request, "Please correct the errors below.")
                return render(request, self.template_name, self.get_context_data(form=form))

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            traceback.print_exc() # Print full traceback to console for debugging
            return render(request, self.template_name, self.get_context_data(form=form if form else UnifiedRequestForm()))
        
    
class SuccessPageView(TemplateView):
    """
    Displays a success message after a request submission.
    Optionally shows details about the submitted request.
    """
    template_name = 'unified_requests/success_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        request_type_slug = self.kwargs.get('request_type')

        request_obj = None
        if pk and request_type_slug:
            # Dynamically fetch the object based on its type
            if request_type_slug == 'complaint':
                model = Complaint
            elif request_type_slug == 'service':
                model = ServiceRequest
            elif request_type_slug == 'inquiry':
                model = Inquiry
            elif request_type_slug == 'emergency':
                model = EmergencyReport
            else:
                model = None # Invalid type

            if model:
                try:
                    request_obj = get_object_or_404(model, pk=pk)
                    # Add request_type_slug to the object if it's not a model property
                    request_obj.request_type_slug = request_type_slug
                except Exception:
                    request_obj = None # Object not found or other error

        context['request_obj'] = request_obj
        context['request_type_slug'] = request_type_slug
        return context