# emergency_reporting/models.py
from django.db import models
from django.conf import settings
from abode.models import TimeStampModel
from unified_requests.constants import STATUS_CHOICES

class EmergencyType(TimeStampModel):
    """
    Defines types of emergencies (e.g., Medical, Security, Fire).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Emergency Type"
        verbose_name_plural = "Emergency Types"
        ordering = ['name']

    def __str__(self):
        return self.name

class EmergencyReport(TimeStampModel):
    """
    Represents an emergency reported by a user.
    """
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='emergency_reports_submitted'
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

    emergency_type = models.ForeignKey(
        EmergencyType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_reports'
    )
    subject = models.CharField(
        max_length=255,
        help_text="A brief summary or title of the complaint."
    )
    description = models.TextField(
        help_text="Detailed description of the complaint, including all relevant information."
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_requests_assigned',
        help_text="Admin/Staff member assigned to this service request."
    )

    attachments = models.FileField(
        upload_to='emergency_attachments/',
        blank=True,
        null=True,
        help_text="Attach relevant files (e.g., photos, documents)."
    )

    location = models.CharField(max_length=255, help_text="Specific location of the emergency.")
    description = models.TextField(help_text="Details of the emergency.")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_reports_responded',
        help_text="Staff member who responded to the emergency."
    )
    action_taken = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Emergency Report"
        verbose_name_plural = "Emergency Reports"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Emergency #{self.id}: {self.emergency_type.name} at {self.location}"

