# service_assistance/models.py
from django.db import models
from django.conf import settings
from abode.models import TimeStampModel

class ServiceType(TimeStampModel):
    """
    Defines types of services (e.g., Transcript Request, IT Support, Housing).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Service Type"
        verbose_name_plural = "Service Types"
        ordering = ['name']

    def __str__(self):
        return self.name

class ServiceRequest(TimeStampModel):
    """
    Represents a request for a specific service.
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_requests_submitted'
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests'
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
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
        related_name='service_requests_assigned',
        help_text="Admin/Staff member assigned to this service request."
    )
    resolution_details = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"Service Request #{self.id}: {self.subject} ({self.get_status_display()})"

# You can add a ServiceRequestUpdate model similar to ComplaintUpdate if needed.