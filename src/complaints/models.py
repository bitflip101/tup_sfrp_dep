# complaints/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from abode.models import TimeStampModel # From abode app's models.py
from unified_requests.constants import STATUS_CHOICES # NEW: Import STATUS_CHOICES

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
    location_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Specific address or location related to the complaint."
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

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
    
    # @property
    # def submitted_at(self):
    #     return self.created_at


class ComplaintUpdate(TimeStampModel):
    """
    Logs updates or actions taken on a specific complaint.
    Includes fields for tracking changes to status, priority, and assignment.
    """
    UPDATE_TYPE_CHOICES = [
        ('comment', 'Comment'),
        ('status_change', 'Status Change'),
        ('assignment_change', 'Assignment Change'),
        ('priority_change', 'Priority Change'),
        ('resolution', 'Resolution'), # Specific type for when it's resolved
    ]

    complaint = models.ForeignKey(
        'Complaint', # Use string reference if Complaint is defined later or in the same file
        on_delete=models.CASCADE,
        related_name='updates',
        help_text="The complaint to which this update applies."
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Consider models.PROTECT if every update MUST have an associated user
        null=True,
        blank=True,
        related_name='complaint_updates_made',
        help_text="The user (admin/staff) who made this update."
    )
    message = models.TextField(
        blank=True, # Allow message to be optional if change type is primary
        help_text="Detailed message or comment about the update."
    )
    is_public = models.BooleanField(
        default=False,
        help_text="If checked, this update will be visible to the complaint's original submitter."
    )
    
    # --- Detailed tracking fields ---
    update_type = models.CharField(
        max_length=20,
        choices=UPDATE_TYPE_CHOICES,
        default='comment',
        help_text="Type of update (e.g., comment, status change, assignment change)."
    )
    
    # Store old/new values for specific changes for audit trails
    old_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Old status if the update was a status change."
    )
    new_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="New status if the update was a status change."
    )
    old_priority = models.CharField(
        max_length=20,
        choices=Complaint.PRIORITY_CHOICES,
        blank=True,
        null=True,
        help_text="Old priority if the update was a priority change."
    )
    new_priority = models.CharField(
        max_length=20,
        choices=Complaint.PRIORITY_CHOICES,
        blank=True,
        null=True,
        help_text="New priority if the update was a priority change."
    )
    # Use string references for foreign keys if 'Complaint' or User might not be defined yet
    old_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='old_assigned_updates',
        help_text="Previous user assigned to the complaint."
    )
    new_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='new_assigned_updates',
        help_text="New user assigned to the complaint."
    )
    # --- End Detailed tracking fields ---

    class Meta(TimeStampModel.Meta):
        verbose_name = "Complaint Update"
        verbose_name_plural = "Complaint Updates"
        # Always order updates by creation time (ascending) to see history chronologically
        ordering = ['submitted_at']

    def __str__(self):
        # Improve __str__ for better readability based on update type
        if self.update_type == 'status_change' and self.old_status and self.new_status:
            return f"Status changed from {self.old_status} to {self.new_status} for Complaint #{self.complaint.id} by {self.updated_by or 'System'}"
        elif self.update_type == 'assignment_change' and self.new_assigned_to:
            return f"Assigned to {self.new_assigned_to.username} for Complaint #{self.complaint.id} by {self.updated_by or 'System'}"
        elif self.update_type == 'priority_change' and self.old_priority and self.new_priority:
            return f"Priority changed from {self.old_priority} to {self.new_priority} for Complaint #{self.complaint.id} by {self.updated_by or 'System'}"
        elif self.update_type == 'resolution':
            return f"Complaint #{self.complaint.id} resolved by {self.updated_by or 'System'}"
        return f"Update for Complaint #{self.complaint.id} by {self.updated_by or 'System'}: {self.message[:50]}..."