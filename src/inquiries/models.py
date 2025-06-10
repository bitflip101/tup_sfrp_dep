# inquiries/models.py
from django.db import models
from django.conf import settings
from abode.models import TimeStampModel

class InquiryCategory(TimeStampModel):
    """
    Defines categories for inquiries (e.g., Admission, Course Info, General).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Inquiry Category"
        verbose_name_plural = "Inquiry Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Inquiry(TimeStampModel):
    """
    Represents a single inquiry made by a user.
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    ]

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inquiries_submitted'
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


    category = models.ForeignKey(
        InquiryCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries'
    )
    subject = models.CharField(max_length=255)
    question = models.TextField()
    answer = models.TextField(blank=True, null=True) # For admin to provide the answer
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
    answered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Inquiry #{self.id}: {self.subject} ({self.get_status_display()})"
