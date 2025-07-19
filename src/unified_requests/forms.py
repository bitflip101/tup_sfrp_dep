# unified_requests/forms.py
from django import forms
from complaints.models import ComplaintCategory
from services.models import ServiceRequest, ServiceType
from inquiries.models import Inquiry, InquiryCategory
from emergencies.models import EmergencyReport, EmergencyType

from django.core.exceptions import ValidationError
from django.urls import reverse_lazy # Use for generating URLs for error messages

class UnifiedRequestForm(forms.Form):
    """
    A single form to handle submission for Complaints, Service Requests, Inquiries, and Emergency Reports.
    Fields are conditionally rendered/validated based on 'request_type'.
    """
    REQUEST_TYPE_CHOICES = [
        ('', '--- Select Request Type ---'), # Default placeholder
        ('complaint', 'Complaint'),
        ('service', 'Service Assistance'),
        ('inquiry', 'Inquiry'),
        ('emergency', 'Emergency Report'),
    ]

    request_type = forms.ChoiceField(
        choices=REQUEST_TYPE_CHOICES,
        label="What kind of request are you submitting?",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_request_type'})
    )

    ##-Checkbox for "Report Anonymously"
    report_anonymously = forms.BooleanField(
        required = False, # A checkbox that toggle value, check=True, notChedked = False
        label = "Report Anonymously",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input','id':'id_report_anonymously'}),
        help_text = "Check this box if you wish to link/log this request to your user account.",
        initial=False
    )

     # Fields for anonymous submissions
    anonymous_full_name = forms.CharField(
        max_length=255,
        required=False, # Conditionally required in clean()
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Your full name (if not logged in)."
    )
    
    anonymous_email = forms.EmailField(
        required=False, # Conditionally required in clean()
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Your email for follow-up (required if not logged in)."
    )
    
    anonymous_phone = forms.CharField(
        max_length=20,
        required=False, # Conditionally required in clean()
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Your phone number for follow-up (optional)."
    )

    # Specific fields for each type
    # Complaint fields
    complaint_category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.all(),
        required=False,
        empty_label="Select a complaint category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Service Assistance fields
    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.all(),
        required=False,
        empty_label="Select a service type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Inquiry fields
    inquiry_category = forms.ModelChoiceField(
        queryset=InquiryCategory.objects.all(),
        required=False,
        empty_label="Select an inquiry category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    question = forms.CharField( # For inquiries, description might be "question"
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        required=False,
        help_text="Type your question here."
    )

    # Emergency Report fields
    emergency_type = forms.ModelChoiceField(
        queryset=EmergencyType.objects.all(),
        required=False,
        empty_label="Select emergency type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    attachments = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'multiple': False, 'class': 'form-control-file'}),
        help_text="Attach relevant files (e.g., photos, documents)."
    )
    
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Specific location of the emergency (e.g., Building A, Room 101)."
    )

    #---Common fields
    subject = forms.CharField(
        max_length=255,
        required=False, # Make all fields required=False by default, handled in clean()
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="A brief summary of your request."
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        required=False,
        help_text="Provide detailed information about your request."
    )

    # --- Checkbox for Privacy Policy Agreement
    privacy_policy_agreement = forms.BooleanField(
        required=True, # This field MUST be checked
        label="I agree to the Privacy Policy",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_privacy_policy_agreement'}),
        help_text="Please check this box if you want to proceed with your submission."
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Initial required state for anonymous fields based on user authentication
        # The JS will handle the dynamic show/hide and client-side 'required' attribute,
        # but backend validation needs to enforce the logic.
        if self.request and self.request.user.is_authenticated:
            # For logged-in users, anonymous contact fields are generally not needed
            # unless they explicitly choose to report anonymously.
            self.fields['anonymous_full_name'].required = False
            self.fields['anonymous_email'].required = False
            self.fields['anonymous_phone'].required = False
            # Default to not anonymous for logged-in users if not specified
            self.fields['report_anonymously'].initial = False
        else:
            # For truly anonymous users (not logged in), they must either choose to be anonymous
            # or be prompted to login/register. The 'report_anonymously' field is visible.
            # We don't set 'required' here, as clean() method handles the conditional logic.
            pass

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        subject = cleaned_data.get('subject')
        description = cleaned_data.get('description') # This will be main content for C, S, E
        question = cleaned_data.get('question')      # This will be main content for I

        report_anonymously = cleaned_data.get('report_anonymously')
        privacy_policy_agreement = cleaned_data.get('privacy_policy_agreement')

        anonymous_full_name = cleaned_data.get('anonymous_full_name')
        anonymous_email = cleaned_data.get('anonymous_email')
        anonymous_phone = cleaned_data.get('anonymous_phone')

          # --- Debugging print statements ---
        print(f"--- UnifiedRequestForm.clean() ---")
        print(f"Request type: {request_type}")
        print(f"Subject: '{subject}'")
        print(f"Description (from form): '{description}'")
        print(f"Question (from form): '{question}'")
        print(f"Report Anonymously: {report_anonymously}")
        print(f"Privacy Policy Agreement: {privacy_policy_agreement}")
        if self.request and self.request.user.is_authenticated:
            print(f"User authenticated: {self.request.user}")
        else:
            print(f"User not authenticated (anonymous).")
        # --- End Debugging print statements ---

        # --- Privacy Policy Agreement Validation ---
        if not privacy_policy_agreement:
            self.add_error('privacy_policy_agreement', "You must agree to the Privacy Policy to proceed.")
            print("Error: Privacy policy not agreed.")

        # --- Anonymous Submission Logic ---
        if self.request and not self.request.user.is_authenticated:
            # User is NOT authenticated (is anonymous)
            if not report_anonymously:
                # If an anonymous user does NOT check "Report Anonymously",
                # they must be prompted to log in or register.
                login_url = reverse_lazy('account_login') # 'account_login' from django-allauth
                register_url = reverse_lazy('account_signup') # 'account_signup' from django-allauth

                self.add_error(
                    None, # This makes it a non-field error
                    ValidationError(
                        f"You must either <a href='{login_url}'>log in</a>, "
                        f"<a href='{register_url}'>register</a>, or check "
                        f"'Report Anonymously' to submit your request.",
                        code='not_authenticated_and_not_anonymous'
                    )
                )
                print("Error: Not authenticated and not anonymous.")
            else:
                # User is NOT authenticated AND HAS checked "Report Anonymously"
                if not anonymous_email:
                    self.add_error('anonymous_email', "An email address is required for follow-up if reporting anonymously.")
                # anonymous_full_name and anonymous_phone remain optional here
                    print("Error: Anonymous email required.")
        elif self.request and self.request.user.is_authenticated:
            # User IS authenticated
            # If they check 'report_anonymously', we respect that.
            # Otherwise, their user account will be linked. No specific anonymous field validation needed here
            # as the view will handle submitted_by based on the checkbox.
            pass

        # General validation for required common fields
        if not request_type:
            self.add_error('request_type', "Please select a request type.")
            print("Error: Request type not selected.")
        if not subject:
            self.add_error('subject', "Subject is required for all request types.")
            print("Error: Subject is empty.")

        # Specific validations based on request_type
        if request_type == 'complaint':
            if not cleaned_data.get('complaint_category'):
                self.add_error('complaint_category', "Complaint category is required.")
                print("Error: Complaint category required.")
            if not description or not description.strip():
                self.add_error('description', "Description is required for complaints.")
            cleaned_data['service_type'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None

        elif request_type == 'service':
            if not cleaned_data.get('service_type'):
                self.add_error('service_type', "Service type is required.")
                print("Error: Service type required.")
            if not description or not description.strip():
                self.add_error('description', "Description is required for service requests.")
                print("Error: Service description empty.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['latitude'] = None
            cleaned_data['longitude'] = None
            cleaned_data['attachments'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None

        elif request_type == 'inquiry':
            if not cleaned_data.get('inquiry_category'):
                self.add_error('inquiry_category', "Inquiry category is required here.")
                print("Error: Inquiry category required.")
            if not question or not question.strip(): # Inquiry uses 'question' instead of 'description'
                self.add_error('question', "Your question is required.")
                print("Error: Inquiry question empty.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['attachments'] = None
            cleaned_data['service_type'] = None
            # cleaned_data['priority'] = None
            cleaned_data['due_date'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None
            cleaned_data['description'] = question # For consistency, you might map question to description if models share it
            print(f"Mapped form's 'question' to model's 'description': '{cleaned_data['description']}'")
        elif request_type == 'emergency':
            if not cleaned_data.get('emergency_type'):
                self.add_error('emergency_type', "Emergency type is required.")
                print("Error: Emergency type required.")
            if not cleaned_data.get('location') or not cleaned_data.get('location').strip():
                self.add_error('location', "Location is required for emergency reports.")
                print("Error: Emergency location empty.")
            if not description or not description.strip():
                self.add_error('description', "Description is required for emergency reports.")
                print("Error: Emergency description empty.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['complaint_priority'] = None
            cleaned_data['location_address'] = None
            cleaned_data['latitude'] = None
            cleaned_data['longitude'] = None
            cleaned_data['attachments'] = None
            cleaned_data['service_type'] = None
            cleaned_data['priority'] = None
            cleaned_data['due_date'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None

            # If user is authenticated and not reporting anonymously, ensure anonymous fields are cleared
        if self.request and self.request.user.is_authenticated and not report_anonymously:
            cleaned_data['anonymous_full_name'] = None
            cleaned_data['anonymous_email'] = None
            cleaned_data['anonymous_phone'] = None
            
        print(f"Form errors after clean: {self.errors.as_json()}") # Final form errors debug
        print(f"--- End UnifiedRequestForm.clean() ---")
        return cleaned_data