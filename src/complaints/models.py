# complaints/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from unified_requests.constants import STATUS_CHOICES 

class ComplaintCategory(models.Model):
    """
    Defines categories for complaints (e.g., Academic, Facilities, Administrative).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(
        blank=True,
        null=True,
        help_text="'Issues related to campus infrastructure, staff or student behavior.'"
    )

    class Meta:
        verbose_name = "Complaint Category"
        verbose_name_plural = "Complaint Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Complaint(models.Model):
    """
    Represents a single complaint submitted by a user.
    """
    # --- Submission Details ---
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_submitted',
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

    # --- Complaint Content ---
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        help_text="The category this complaint belongs to."
    )
    subject = models.CharField(
        max_length=255,
        help_text="A brief summary or title of the complaint."
    )
    description = models.TextField(
        help_text="Detailed description of the complaint, including all relevant information."
    )
    attachments = models.FileField(
        upload_to='complaints_attachments/',
        blank=True,
        null=True,
        help_text="Attach relevant files (e.g., photos, documents)."
    )

    # --- Status & Priority ---
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES, # Using the imported choices
        default='new', # Initial status for new complaints
        help_text="Current status of the complaint."
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the complaint (e.g., for staff action)."
    )

    # --- Assignment & Resolution ---
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_assigned',
        help_text="Staff member or admin assigned to handle this complaint."
    )
    resolution_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details regarding how the complaint was resolved."
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date and time the complaint was marked as resolved."
    )

    # --- Location Details (Optional, moved for better flow) ---
    # location_address = models.CharField(
    #     max_length=255,
    #     blank=True,
    #     null=True,
    #     help_text="Specific address or location related to the complaint."
    # )
    # latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    # longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    request_type_slug = models.CharField(max_length=50, default='complaint', editable=False)

    def save(self, *args, **kwargs):
        # This ensures the slug is set for new objects
        if not self.request_type_slug:
            self.request_type_slug = 'complaint'
        super().save(*args, **kwargs)

    class Meta():
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ['-submitted_at'] # Order newest first

    def __str__(self):
        return f"Complaint #{self.id}: {self.subject} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        return reverse('complaints:complaint_detail', args=[str(self.pk)])
    
    @property
    def is_anonymous_submission(self):
        # A complaint is anonymous if submitted_by is None AND contact details are provided.
        # This prevents complaints with no info from being 'anonymous'.
        return self.submitted_by is None and (self.full_name or self.email or self.phone_number)
