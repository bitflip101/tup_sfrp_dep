# support_dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import DateInput # NEW: For HTML5 date input

# Import your unified STATUS_CHOICES
from unified_requests.constants import STATUS_CHOICES

# Get the currently active user model
User = get_user_model()

# NEW: Define REQUEST_TYPE_CHOICES for filtering by request type
# These should align with the slugs used in your models (e.g., Complaint.REQUEST_TYPE_SLUG)
REQUEST_TYPE_CHOICES = (
    ('', 'All Types'), # Option to not filter by type
    ('complaint', 'Complaint'),
    ('service', 'Service Request'),
    ('inquiry', 'Inquiry'),
    ('emergency', 'Emergency Report'),
)

# Existing Form for updating request status in detail view
class RequestStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Existing Form for updating request assignment in detail view
class RequestAssignmentUpdateForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        # IMPORTANT CHANGE: Only show staff users as assignable agents
        queryset=User.objects.filter(is_staff=True).order_by('first_name', 'last_name'),
        required=False, # Assignment can be optional (e.g., unassign)
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Unassigned" # Option for unassigning
    )

# NEW: Form for Search and Filtering on the Request List Page
class RequestFilterForm(forms.Form):
    # Search field for ID, Subject, Description
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'ID, Subject, or Description'})
    )

    # Filter by Status
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, # Reusing the STATUS_CHOICES from constants
        required=False,
        label='Status'
    )

    # Filter by Assigned Agent (only staff users)
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True).order_by('first_name', 'last_name'),
        required=False,
        label='Assigned To',
        empty_label='All Agents' # Option for no specific agent
    )

    # Filter by Submission Date Range
    submitted_after = forms.DateField(
        required=False,
        label='Submitted After',
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}) # Added form-control class
    )
    submitted_before = forms.DateField(
        required=False,
        label='Submitted Before',
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}) # Added form-control class
    )

    # Filter by Request Type
    request_type = forms.ChoiceField(
        choices=REQUEST_TYPE_CHOICES,
        required=False,
        label='Request Type'
    )

    # Checkbox to show only unassigned requests
    show_unassigned = forms.BooleanField(
        required=False,
        label='Show Unassigned Only',
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Add Bootstrap classes to all default widgets for consistency
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.ClearableFileInput)):
                # Apply form-control class to most widgets
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                # Ensure checkbox input has its appropriate class
                field.widget.attrs.update({'class': 'form-check-input'})