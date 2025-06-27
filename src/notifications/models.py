from django.db import models


# Model to keep track of overdue notifications sent to prevent spamming
class OverdueNotificationLog(models.Model):
    request_type = models.CharField(max_length=50) # e.g., 'complaint', 'emergency'
    request_id = models.IntegerField()
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure only one notification log entry per request per specific overdue event
        unique_together = ('request_type', 'request_id')
        ordering = ['-notified_at']

    def __str__(self):
        return f"Overdue notification for {self.request_type} #{self.request_id} at {self.notified_at}"
