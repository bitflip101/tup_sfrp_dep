from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging

# Helper function to strip HTML tags for plain text email (add to notifications/utils.py)
from django.utils.html import strip_tags

# Import your request models here
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

# Get an instance of a logger
logger = logging.getLogger(__name__)

def send_request_status_update_email(request_obj, old_status, new_status):
    """
    Sends an email to the user when their request status is updated.
    """
    # Determine the choices for the status field from the request_obj's specific model
    # This ensures we get the correct choices even if models have slightly different status sets
    try:
        status_choices_map = dict(request_obj._meta.get_field('status').choices)
    except Exception as e:
        # Fallback in case 'status' field or choices are not found (unlikely if your models are consistent)
        print(f"Warning: Could not retrieve status choices for {request_obj.__class__.__name__}. Error: {e}")
        status_choices_map = {} # Provide an empty map as a safe fallback

    # Get the human-readable display values using the map
    # .get(key, default) is used in case a status value isn't perfectly mapped (e.g., a typo)
    old_status_display = status_choices_map.get(old_status, old_status) # Fallback to raw value if display not found
    new_status_display = status_choices_map.get(new_status, new_status)

    user_name = request_obj.submitted_by.get_full_name() if request_obj.submitted_by else (request_obj.full_name or 'Valued User')
    recipient_email = request_obj.submitted_by.email if request_obj.submitted_by else request_obj.email

    if not recipient_email:
        # No email to send to
        return

    request_url = settings.BASE_URL + reverse(
        'support_dashboard:request_detail',
        kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk}
    )

    context = {
        'user_name': user_name,
        'request_id': request_obj.pk,
        'request_subject': request_obj.subject,
        'old_status': old_status_display, # Use the correctly obtained display value
        'new_status': new_status_display, # Use the correctly obtained display value
        'request_url': request_url,
    }

    user_subject = f"Your Request #{request_obj.pk} Status Update: {new_status_display}"
    user_html_content = render_to_string('notifications/request_status_update_user_email.html', context)
    user_text_content = strip_tags(user_html_content)

    user_msg = EmailMultiAlternatives(
        user_subject,
        user_text_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )
    user_msg.attach_alternative(user_html_content, "text/html")
    user_msg.send()

def send_request_assignment_email(request_obj):
    """
    Sends an email to the newly assigned staff member.
    """
    if not request_obj.assigned_to or not request_obj.assigned_to.email:
        return # No one assigned or assigned person has no email

    assigned_staff_name = request_obj.assigned_to.get_full_name() or request_obj.assigned_to.username
    recipient_email = request_obj.assigned_to.email

    request_url = settings.BASE_URL + reverse(
        'support_dashboard:request_detail',
        kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk} # Ensure request_type_slug is available
    )

    context = {
        'assigned_staff_name': assigned_staff_name,
        'request_id': request_obj.pk,
        'request_type': request_obj.request_type_slug.replace('_', ' ').title(), # Make it readable (e.g., "Service Request")
        'request_subject': request_obj.subject,
        'request_status': request_obj.get_status_display(),
        'request_url': request_url,
    }

    subject = f"New Request Assigned To You: #{request_obj.pk} - {request_obj.subject}"
    html_content = render_to_string('notifications/request_assigned_to_staff_email.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

# NEW/REFINED FUNCTION for initial submission notifications
def send_new_request_submission_notifications(request_obj):
    """
    Sends notification emails upon initial submission of any request type:
    - To the user who submitted the request (confirmation).
    - To an admin/support email (new request alert).
    """
    # Ensure request_type_slug is set on the object
    if not hasattr(request_obj, 'request_type_slug'):
        if isinstance(request_obj, Complaint):
            request_obj.request_type_slug = 'complaint'
        elif isinstance(request_obj, ServiceRequest):
            request_obj.request_type_slug = 'service'
        elif isinstance(request_obj, Inquiry):
            request_obj.request_type_slug = 'inquiry'
        elif isinstance(request_obj, EmergencyReport):
            request_obj.request_type_slug = 'emergency'
        else:
            request_obj.request_type_slug = 'unknown' # Fallback for unexpected types

    # --- Email to the User (Submission Confirmation) ---
    recipient_email = request_obj.submitted_by.email if request_obj.submitted_by else request_obj.email
    user_name = request_obj.submitted_by.get_full_name() or request_obj.submitted_by.username if request_obj.submitted_by else (request_obj.full_name or 'Valued User')

    if recipient_email:
        # Link to the user's specific request detail page (can be in unified_requests or a user dashboard)
        # Assuming you have a user-facing detail URL like 'unified_requests:request_detail'
        try:
            user_request_url = settings.BASE_URL + reverse(
                'unified_requests:request_detail',
                kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk}
            )
        except Exception:
            user_request_url = settings.BASE_URL # Fallback if URL reverse fails

        user_context = {
            'user_name': user_name,
            'request_id': request_obj.pk,
            'request_type': request_obj.request_type_slug.replace('_', ' ').title(),
            'request_subject': request_obj.subject,
            'request_url': user_request_url,
            'request_description': request_obj.description, # Include description
            # Add other details relevant to the user's confirmation email
        }
        user_subject = f"Your Request #{request_obj.pk} Has Been Submitted Successfully"
        # Use a generic template, you might need to rename/adapt your existing ones
        user_html_content = render_to_string('notifications/request_submitted_user_email.html', user_context)
        user_text_content = strip_tags(user_html_content)

        user_msg = EmailMultiAlternatives(
            user_subject,
            user_text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email]
        )
        user_msg.attach_alternative(user_html_content, "text/html")
        user_msg.send()

    # --- Email to Admin/Support (New Request Alert) ---
    # You need to define ADMIN_EMAIL_FOR_NOTIFICATIONS in your settings.py
    admin_recipient_email = getattr(settings, 'ADMIN_EMAIL_FOR_NOTIFICATIONS', None)
    if admin_recipient_email:
        # Link to the admin dashboard detail view
        try:
            admin_dashboard_url = settings.BASE_URL + reverse(
                'support_dashboard:request_detail',
                kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk}
            )
        except Exception:
            admin_dashboard_url = settings.BASE_URL + '/dashboard/' # Fallback if URL reverse fails

        admin_context = {
            'request_id': request_obj.pk,
            'request_type': request_obj.request_type_slug.replace('_', ' ').title(),
            'request_subject': request_obj.subject,
            'submitted_by': user_name,
            'submitted_email': recipient_email,
            'admin_dashboard_url': admin_dashboard_url,
            'request_description': request_obj.description, # Include description
            # Add other details pertinent to admin alert
        }
        admin_subject = f"New {request_obj.request_type_slug.replace('_', ' ').title()} Submitted: #{request_obj.pk} - {request_obj.subject}"
        # Use a generic template, you might need to rename/adapt your existing ones
        admin_html_content = render_to_string('notifications/request_submitted_admin_email.html', admin_context)
        admin_text_content = strip_tags(admin_html_content)

        admin_msg = EmailMultiAlternatives(
            admin_subject,
            admin_text_content,
            settings.DEFAULT_FROM_EMAIL,
            [admin_recipient_email]
        )
        admin_msg.attach_alternative(admin_html_content, "text/html")
        admin_msg.send()