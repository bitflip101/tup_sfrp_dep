# support_dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model # To get the User model dynamically
from django.forms.widgets import DateInput
from django.contrib.auth.models import Group # Import Group model

# Import your unified STATUS_CHOICES
from unified_requests.constants import STATUS_CHOICES

# Import your category models
from complaints.models import ComplaintCategory
from services.models import ServiceType
from inquiries.models import InquiryCategory
from emergencies.models import EmergencyType

# Import FAQ models
from faqs.models import FAQCategory, FAQItem

# Get the currently active user model
User = get_user_model()

# Define REQUEST_TYPE_CHOICES for filtering by request type
REQUEST_TYPE_CHOICES = (
    ('', 'All Types'),
    ('complaint', 'Complaint'),
    ('service', 'Service Request'),
    ('inquiry', 'Inquiry'),
    ('emergency', 'Emergency Report'),
)

# --- Forms for All Request---
class RequestStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class RequestAssignmentUpdateForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True).order_by('first_name', 'last_name'),
        required=False,
        empty_label="Unassigned",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class RequestFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'ID, Subject, or Description'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True).order_by('first_name', 'last_name'),
        required=False,
        label='Assigned To',
        empty_label='All Agents'
    )
    submitted_after = forms.DateField(
        required=False,
        label='Submitted After',
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    submitted_before = forms.DateField(
        required=False,
        label='Submitted Before',
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    request_type = forms.ChoiceField(
        choices=REQUEST_TYPE_CHOICES,
        required=False,
        label='Request Type'
    )
    show_unassigned = forms.BooleanField(
        required=False,
        label='Show Unassigned Only',
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.ClearableFileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

# --- ModelForms for Request Type/Category Management ---
class ComplaintCategoryForm(forms.ModelForm):
    class Meta:
        model = ComplaintCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Category Name',
            'description': 'Category Description',
        }

class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Service Type Name',
            'description': 'Service Type Description',
        }

class InquiryCategoryForm(forms.ModelForm):
    class Meta:
        model = InquiryCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Category Name',
            'description': 'Category Description',
        }

class EmergencyTypeForm(forms.ModelForm):
    class Meta:
        model = EmergencyType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Emergency Type Name',
            'description': 'Emergency Type Description',
        }

# Dictionary to easily map slugs to ModelForms
CATEGORY_FORMS = {
    'complaint': ComplaintCategoryForm,
    'service': ServiceTypeForm,
    'inquiry': InquiryCategoryForm,
    'emergency': EmergencyTypeForm,
}

# --- Forms for User Management ---
class UserAdminForm(forms.ModelForm):
    """
    Form for managing user details (for admin/superuser).
    Does NOT include password fields directly for security/simplicity.
    Password changes should be handled separately or through Django Allauth's reset flow.
    """
    # Use CharField for password input when creating a user, then set it in view.
    # This field is NOT part of the model directly, it's for form processing only.
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False, # Required only on creation, not on update
        help_text="Password will be automatically set to a default if left blank on creation. For existing users, leave blank to keep current password."
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Confirm password for new user. Must match."
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'is_active', 'groups'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control'}), # For multi-select groups
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'email': 'Required. Used for login and notifications.',
            'is_staff': 'Designates whether the user can log into this admin site.',
            'is_superuser': 'Designates that this user has all permissions without explicitly assigning them.',
            'is_active': 'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
            'groups': 'The groups this user belongs to. A user will get all permissions granted to each of their groups.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make username and email required for all operations
        self.fields['username'].required = True
        self.fields['email'].required = True

        # If updating an existing user, password fields are not strictly required unless changed
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = "Leave blank to keep current password."
        else:
            # For new user creation, password is required
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
            self.fields['password'].help_text = "Required for new users."
            self.fields['confirm_password'].help_text = "Required for new users. Must match."

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Validate passwords only if both are provided
        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
        elif (password and not confirm_password) or (not password and confirm_password):
            self.add_error('confirm_password', "Please confirm the password.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        # Set password only if a new password was provided
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            # Handle groups m2m separately after user save for new users
            if 'groups' in self.cleaned_data:
                user.groups.set(self.cleaned_data['groups'])
        return user

class UserCreateForm(UserAdminForm):
    """
    Specific form for creating new users, ensuring password fields are required.
    """
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text="Required. Set a password for the new user."
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text="Required. Confirm the password for the new user. Must match."
    )

    # Override __init__ to explicitly set required to True for passwords on creation
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = True
        self.fields['confirm_password'].required = True
        self.fields['password'].help_text = "Required. Set a password for the new user."
        self.fields['confirm_password'].help_text = "Required. Confirm the password for the new user. Must match."

# --- Form for Group Management ---
class GroupForm(forms.ModelForm):
    """
    Form for managing Django authentication Groups.
    """
    class Meta:
        model = Group
        fields = ['name'] # Groups only have a 'name' field by default
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Group Name',
        }
        help_texts = {
            'name': 'The name of the group. Should be unique.',
        }

# --- Forms for FAQ Management ---
class FAQCategoryForm(forms.ModelForm):
    class Meta:
        model = FAQCategory
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Category Name',
            'order': 'Display Order',
        }
        help_texts = {
            'order': 'Lower numbers appear first.',
        }

class FAQItemForm(forms.ModelForm):
    class Meta:
        model = FAQItem
        fields = ['category', 'question', 'answer', 'is_published', 'order', 'tags']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            # Taggit's default widget is usually fine, but can customize if needed
            # 'tags': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'category': 'FAQ Category',
            'question': 'Question',
            'answer': 'Answer',
            'is_published': 'Publish on Website',
            'order': 'Display Order',
            'tags': 'Tags (comma-separated)', # Label for tags
        }
        help_texts = {
            'order': 'Lower numbers appear first within its category.',
            'tags': 'Enter tags separated by commas (e.g., "Academic Issues, Grades, Complaints").', # Help text for tags
        }
