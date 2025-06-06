from django.db import models

class TimeStampModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.

    This model is designed to be inherited by other models that need
    automatic timestamping for creation and last modification times.
    Because it's an abstract class, it won't create a separate table in the database;
    instead, its fields will be included in the tables of any models that inherit from it.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,  # Automatically sets the field to the current datetime when the object is first created.
        editable=False,     # Makes this field non-editable in the Django admin and forms.
        verbose_name="Created At",
        help_text="The date and time when this object was first created."
    )

    # Field name 'updated_at' is typically used
    # auto_now=True updates the date/time every time the object is saved
    updated_at = models.DateTimeField(
        auto_now=True,      # Automatically updates the field to the current datetime every time the object is saved.
        verbose_name="Updated At",
        help_text="The date and time when this object was last updated."
    )

    class Meta:
        """
        Meta options for the TimeStampModel.
        """
        abstract = True         # This is crucial! It tells Django not to create a separate table for this model.
                                # Instead, its fields will be added to the concrete models that inherit from it.
        ordering = ['-created_at'] # Default ordering for models inheriting this, showing newest first.
                                   # You can override this in child models' Meta classes.
        verbose_name = "Timestamped Object" # A human-readable name for the model in the admin, if it were concrete.
        verbose_name_plural = "Timestamped Objects"


# Example of how you would use it in another app's models.py (e.g., complaints/models.py)
# from core.models import TimeStampModel
#
# class Complaint(TimeStampModel):
#     # Your Complaint model fields go here
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     status = models.CharField(max_length=50, default='New')
#     # ... other fields
#
#     def __str__(self):
#         return self.title
#
#     class Meta(TimeStampModel.Meta): # Inherit Meta options (like ordering)
#         verbose_name = "Complaint"
#         verbose_name_plural = "Complaints"
#         # You can override ordering here if needed:
#         # ordering = ['status', '-created_at']
