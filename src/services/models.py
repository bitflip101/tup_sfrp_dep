# service_assistance/models.py
from django.db import models
from django.conf import settings
from abode.models import TimeStampModel
from unified_requests.constants import STATUS_CHOICES

class ServiceType(models.Model):
    """
    Defines types of services (e.g., Transcript Request, IT Support, ID Card..).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="A bried description of service type, e.g., 'services need from school.'")

    class Meta:
        verbose_name = "Service Type"
        verbose_name_plural = "Service Types"
        ordering = ['name']

    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    """
    Represents a request for a specific service.
    """
    # --- Submission Details ---
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_requests_submitted',
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

    # --- Service Type Content ---
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests',
        help_text="The service type this service request belongs to."
    )
    subject = models.CharField(
        max_length=255,
        help_text="A brief summary or title of the service request."
        )
    description = models.TextField(
        help_text="Detailed description of the service being requested, including all relevant information."
    )
    attachments = models.FileField(
        upload_to='service_requests_attachments/',
        blank=True,
        null=True,
        help_text="Attach relevant files (e.g., photos, documents)."
    )

    # --- Status and Priority
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the service request. (e.g., for staff action)."
    )

    # --- Assignment & Resolution
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests_assigned',
        help_text="Admin/Staff member assigned to this service request."
    )
    resolution_details = models.TextField(
        blank=True, 
        null=True,
        help_text="Details regarding how the service request was resolved."
        )
    resolved_at = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="The date and time the complaint was marked as resolved."
        )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Service Request #{self.id}: {self.subject} ({self.get_status_display()})"
    
    
    
    @property
    def is_anonymous_submission(self):
        # A complaint is anonymous if submitted_by is None AND contact details are provided.
        # This prevents complaints with no info from being 'anonymous'.
        return self.submitted_by is None and (self.full_name or self.email or self.phone_number)

