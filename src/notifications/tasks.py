# notifications/tasks.py
from django.db import models
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import OverdueNotificationLog

# Import all your request models
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

User = get_user_model()    

@shared_task
def check_overdue_requests():
    """
    Celery task to check for overdue requests and send notifications to staff.
    A request is considered overdue if its status is not 'resolved', 'closed', or 'rejected'
    and it hasn't been updated for 48 hours.
    """
    overdue_threshold = timezone.now() - timedelta(hours=48)
    not_final_statuses = ['new', 'in_progress'] # Define statuses that require action

    request_models = {
        'complaint': Complaint,
        'service_request': ServiceRequest,
        'inquiry': Inquiry,
        'emergency': EmergencyReport,
    }

    overdue_requests_to_notify = []

    for request_type, Model in request_models.items():
        # Get requests that are in a non-final status and haven't been updated recently
        potential_overdue_requests = Model.objects.filter(
            status__in=not_final_statuses,
            updated_at__lt=overdue_threshold
        )

        for req in potential_overdue_requests:
            # Check if this specific request has already been notified as overdue
            # since its last update
            last_notification = OverdueNotificationLog.objects.filter(
                request_type=request_type,
                request_id=req.pk
            ).order_by('-notified_at').first()

            if last_notification is None or last_notification.notified_at < req.updated_at:
                # If no previous notification, or if the request was updated AFTER
                # the last notification (meaning it became overdue again)
                overdue_requests_to_notify.append({
                    'type': request_type.replace('_', ' ').title(),
                    'pk': req.pk,
                    'subject': getattr(req, 'subject', f"Request #{req.pk}"), # Use subject if exists, else ID
                    'link': settings.BASE_URL + f"/notifications/{request_type.replace('_', '-')}/{req.pk}/",
                    'last_updated': req.updated_at,
                    'status': req.get_status_display(),
                    'full_obj': req # Keep full object for logging later
                })

    if overdue_requests_to_notify:
        admin_emails = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
        admin_emails = [email for email in admin_emails if email] # Remove empty emails

        if not admin_emails:
            print("No active staff users with emails found to notify.")
            return

        print(f"Found {len(overdue_requests_to_notify)} overdue requests. Notifying admins.")

        for req_data in overdue_requests_to_notify:
            subject = f"Urgent: Overdue {req_data['type']} #{req_data['pk']} - {req_data['subject']}"
            html_message = render_to_string(
                'notifications/overdue_notification_email.html',
                {'request_data': req_data, 'admin_link': settings.BASE_URL + '/admin/'}
            )
            plain_message = f"Request Type: {req_data['type']}\n" \
                            f"ID: {req_data['pk']}\n" \
                            f"Subject: {req_data['subject']}\n" \
                            f"Last Updated: {req_data['last_updated']}\n" \
                            f"Status: {req_data['status']}\n" \
                            f"View Details: {req_data['link']}"
            # --- Settings flags 
            if getattr(settings, 'NOTIFICATIONS_SEND_EMAILS', False):
                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails, # Send to all admins
                        html_message=html_message,
                        fail_silently=False,
                    )
                    print(f"Notification sent for {req_data['type']} #{req_data['pk']}")
                except Exception as e:
                    print(f"Error sending email for {req_data['type']} #{req_data['pk']}: {e}")
            else:
                print(f"DEBUG: Email sending is disabled. Would have sent email for {req_data['type']} #{req_data['pk']}")

                # Log that the notification was sent (or would have been sent) for this request
                OverdueNotificationLog.objects.create(
                    request_type=req_data['full_obj'].request_type_slug,
                    request_id=req_data['full_obj'].pk
                )
    else:
        print("No overdue requests found.")