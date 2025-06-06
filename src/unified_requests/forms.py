# unified_requests/forms.py
from django import forms
from complaints.models import ComplaintCategory
from services.models import ServiceType
from inquiries.models import InquiryCategory
from emergencies.models import EmergencyType

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

    # Common fields
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

    # Specific fields for each type
    # Complaint fields
    complaint_category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.all(),
        required=False,
        empty_label="Select a complaint category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    complaint_priority = forms.ChoiceField(
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        required=False,
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
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Specific location of the emergency (e.g., Building A, Room 101)."
    )

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        subject = cleaned_data.get('subject')
        description = cleaned_data.get('description') # This will be main content for C, S, E
        question = cleaned_data.get('question')      # This will be main content for I

        # General validation for required common fields
        if not request_type:
            self.add_error('request_type', "Please select a request type.")
        if not subject:
            self.add_error('subject', "Subject is required for all request types.")

        # Specific validations based on request_type
        if request_type == 'complaint':
            if not cleaned_data.get('complaint_category'):
                self.add_error('complaint_category', "Complaint category is required.")
            if not description:
                self.add_error('description', "Description is required for complaints.")
            if not cleaned_data.get('complaint_priority'):
                self.add_error('complaint_priority', "Priority is required for complaints.")
            # Clear other fields to avoid confusion later
            cleaned_data['service_type'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None

        elif request_type == 'service':
            if not cleaned_data.get('service_type'):
                self.add_error('service_type', "Service type is required.")
            if not description:
                self.add_error('description', "Description is required for service requests.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['complaint_priority'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None

        elif request_type == 'inquiry':
            if not cleaned_data.get('inquiry_category'):
                self.add_error('inquiry_category', "Inquiry category is required.")
            if not question: # Inquiry uses 'question' instead of 'description'
                self.add_error('question', "Your question is required.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['complaint_priority'] = None
            cleaned_data['service_type'] = None
            cleaned_data['description'] = None
            cleaned_data['emergency_type'] = None
            cleaned_data['location'] = None
            # Set description to question for easier processing in view
            cleaned_data['description'] = question # Use question for processing

        elif request_type == 'emergency':
            if not cleaned_data.get('emergency_type'):
                self.add_error('emergency_type', "Emergency type is required.")
            if not cleaned_data.get('location'):
                self.add_error('location', "Location is required for emergency reports.")
            if not description:
                self.add_error('description', "Description is required for emergency reports.")
            # Clear other fields
            cleaned_data['complaint_category'] = None
            cleaned_data['complaint_priority'] = None
            cleaned_data['service_type'] = None
            cleaned_data['inquiry_category'] = None
            cleaned_data['question'] = None

        return cleaned_data