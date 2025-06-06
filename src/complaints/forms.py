# complaints/forms.py
from django import forms
from .models import Complaint, ComplaintUpdate, ComplaintCategory
from config import settings

class ComplaintForm(forms.ModelForm):
    """
    Form for users to submit a new complaint.
    """

    # This will automatically render a dropdown for categories
    # You might want to make it required or optional based on your needs.
    # The 'empty_label' provides an option for no category selected.
    category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.all().order_by('name'),
        empty_label="Select a Category",
        required=True, # Make it required for submission
        widget=forms.Select(attrs={'class': 'form-control'}) # Add Bootstrap class
    )

    class Meta:
        model = Complaint
        fields = ['category', 'subject', 'description', 'priority'] # Users typically set priority, if desired
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Add Bootstrap classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class ComplaintUpdateForm(forms.ModelForm):
    """
    Form for administrators to add updates to a complaint.
    """
    class Meta:
        model = ComplaintUpdate
        fields = ['message', 'is_public']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

# Form for admin to change complaint status, assign, or add resolution details
class ComplaintAdminUpdateForm(forms.ModelForm):
    """
    Form for administrators to update status, assignment, and resolution details of a complaint.
    """
    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'assigned_to', 'resolution_details']
        widgets = {
            'resolution_details': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        # Filter assigned_to to show only staff/admin users (assuming 'accounts' app defines user types)
        # This requires integrating with the accounts app's User model
        if 'assigned_to' in self.fields:
            # Assuming 'accounts' app has a User model with an 'is_staff' or 'user_type' attribute
            self.fields['assigned_to'].queryset = settings.AUTH_USER_MODEL.objects.filter(is_staff=True) # Or user_type__name='Admin'
