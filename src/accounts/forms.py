# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser # Import your custom user model

# Custom User Creation Form for Registration
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # IMPORTANT: Add 'user_type' here
        fields = ('email', 'first_name', 'last_name', 'user_type',) # <--- Added 'user_type'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes and Placeholders for all visible fields
        field_attrs = {
            'class': 'form-control',
        }

        self.fields['email'].widget.attrs.update(field_attrs)
        self.fields['email'].widget.attrs['placeholder'] = 'Email Address'
        self.fields['password1'].widget.attrs.update(field_attrs)
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs.update(field_attrs)
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs.update(field_attrs)
            self.fields['first_name'].widget.attrs['placeholder'] = 'First Name (Optional)'
            self.fields['first_name'].required = False # Make first name optional if desired
            self.fields['first_name'].label = '' # Remove default label

        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs.update(field_attrs)
            self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name (Optional)'
            self.fields['last_name'].required = False # Make last name optional if desired
            self.fields['last_name'].label = '' # Remove default label

        # NEW: Apply styling and hide label for 'user_type'
        if 'user_type' in self.fields:
            self.fields['user_type'].widget.attrs.update(field_attrs)
            # For a select field, a placeholder isn't standard, but we can add a default option
            # This is typically handled by the widget itself or by adding an empty choice.
            # Bootstrap's form-select class will style it.
            self.fields['user_type'].label = '' # Hide the label

        # Set all labels to empty strings to hide them, relying on placeholders
        self.fields['email'].label = ''
        self.fields['password1'].label = ''
        self.fields['password2'].label = ''
        # (first_name, last_name, user_type labels already handled above)

# Custom Authentication Form for Login (no changes needed here for user_type)
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['username'].label = ''
        self.fields['password'].label = ''