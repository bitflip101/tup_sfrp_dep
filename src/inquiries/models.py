# inquiries/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from abode.models import TimeStampModel
from unified_requests.constants import STATUS_CHOICES

class InquiryCategory(models.Model):
    """
    Defines categories for inquiries (e.g., Admission, Course Info, General).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="'A brief of your inquiry.'")

    class Meta:
        verbose_name = "Inquiry Category"
        verbose_name_plural = "Inquiry Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Inquiry(models.Model):
    """
    Represents a single inquiry made by a user.
    """
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries_submitted',
        help_text="Authenticated user who submitted the complaint (if any)."
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full name of the submitter (for anonymous or guest submissions)."
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address of the submitter (for anonymous or guest submissions)."
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number of the submitter (for anonymous or guest submissions)."
    )

    # --- Inquiry Content ----
    category = models.ForeignKey(
        InquiryCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries'
    )
    subject = models.CharField(
        max_length=255,
        help_text="A brief summary or title of inquiry.")
    description = models.TextField()
    answer = models.TextField(blank=True, null=True) # For admin to provide the answer

    attachments = models.FileField(
        upload_to='inquiry_attachments/',
        blank=True,
        null=True,
        help_text="Attach relevant files (e.g., photos, documents)."
    )

    # --- Status & Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries_assigned',
        help_text="Admin/Staff member assigned to this inquiry."
    )
    resolution_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details regarding how the inquiry was resolved."
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date and time the inquiry was marked as resolved."
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    request_type_slug = models.CharField(max_length=50, default='inquiry', editable=False)

    def save(self, *args, **kwargs):
        if not self.request_type_slug:
            self.request_type_slug = 'inquiry' # Ensure this matches the key in tasks.py
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"
        ordering = ['-submitted_at']

    class Meta():
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"
        ordering = ['-submitted_at'] # Order newest first

    def __str__(self):
        return f"Inquiry #{self.id}: {self.subject} ({self.get_status_display()})"
    
    @property
    def is_anonymous_submission(self):
        # A complaint is anonymous if submitted_by is None AND contact details are provided.
        # This prevents complaints with no info from being 'anonymous'.
        return self.submitted_by is None and (self.full_name or self.email or self.phone_number)
