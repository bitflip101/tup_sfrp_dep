# user_dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their profile information.
    """
    class Meta:
        model = User
        # Include fields you want the user to be able to edit.
        # Avoid sensitive fields like password directly here.
        fields = ['first_name', 'last_name', 'email']
        # You might want to make email read-only if allauth handles email verification separately
        # or if you prefer users to change email through allauth's specific email management flow.
        # widgets = {
        #     'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            # If you want to make email read-only for authenticated users
            # if field_name == 'email' and self.instance and self.instance.pk:
            #     field.widget.attrs['readonly'] = 'readonly'
            #     field.help_text = "Email address cannot be changed here. Please use the email management section if available."

    def clean_email(self):
        """
        Custom validation for email to ensure uniqueness if it's being changed.
        Django's ModelForm handles uniqueness by default, but this is an example
        if you needed more custom logic or to prevent changing if allauth handles it.
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use by another account.")
        return email

