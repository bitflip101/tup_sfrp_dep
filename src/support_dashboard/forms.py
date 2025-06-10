# support_dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model
from unified_requests.constants import STATUS_CHOICES


User = get_user_model() # Get the currently active user model

class RequestStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class RequestAssignmentUpdateForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(), # Query all users to assign to
        required=False, # Assignment can be optional (e.g., unassign)
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Unassigned" # Option for unassigning
    )