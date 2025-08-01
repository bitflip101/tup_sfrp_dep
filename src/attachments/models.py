# attachments/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings # To get the User model if needed for 'uploaded_by'

class RequestAttachment(models.Model):
    # This will store the actual file
    file = models.FileField(upload_to='attachments/') # Files will be stored in MEDIA_ROOT/attachments/

    # Generic Foreign Key to link to any content type (e.g., Complaint, ServiceRequest)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_attachments'
    )

    def __str__(self):
        return f"Attachment for {self.content_type.model} ID {self.object_id} - {self.file.name}"

    class Meta:
        verbose_name = "Request Attachment"
        verbose_name_plural = "Request Attachments"
