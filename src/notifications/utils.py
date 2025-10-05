from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
# from django.utils.html import strip_tags
from django.urls import reverse
import logging

# Helper function to strip HTML tags for plain text email (add to notifications/utils.py)
from django.utils.html import strip_tags

# Import request models here
from complaints.models import Complaint
from services.models import ServiceRequest
from inquiries.models import Inquiry
from emergencies.models import EmergencyReport

# Need to import ContentType for dynamically generating admin URLs
from django.contrib.contenttypes.models import ContentType

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Send email to user when request has been updated or status changed.
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
    if request_obj.submitted_by:
        full_name = request_obj.submitted_by.get_full_name()
        if full_name:
            user_name = full_name
        else:
            # Fallback to username if get_full_name()is empty (e.g., first_name/last_name not set)
            user_name = request_obj.submitted_by.username
    elif request_obj.full_name: # For anonymous submissions where a name was provided
        user_name = request_obj.full_name
    new_status_display = status_choices_map.get(new_status, new_status)

    # user_name = request_obj.submitted_by.get_full_name() if request_obj.submitted_by else (request_obj.full_name or 'Valued User')

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
        'request_type': request_obj.request_type_slug.replace('_', ' ').title(), # for template
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

# Send email to sfaff/support when request has been assigned to the group.
def send_request_assignment_email(request_obj):
    """
    Sends an email to the newly assigned staff member.
    """
    if not request_obj.assigned_to or not request_obj.assigned_to.email:
        return # No one assigned or assigned person has no email

    assigned_staff_name = request_obj.assigned_to.get_full_name() or request_obj.assigned_to.username
    recipient_email = request_obj.assigned_to.email

    request_url = settings.BASE_URL + reverse('support_dashboard:request_detail',
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

# FUNCTION for initial submission notifications
def send_new_request_submission_notifications(request_obj):
    """
    Sends notification emails upon initial submission of any request type:
    - To the user who submitted the request (confirmation).
    - To an admin/support email (new request alert).
    """
    # Ensure request_type_slug is set on the object
    if not hasattr(request_obj, 'request_type_slug') or not request_obj.request_type_slug:
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
                kwargs={'request_type_slug': request_obj.request_type_slug, 'pk': request_obj.pk}
            )
        except Exception as e:
            print(f"Error reversing user request URL: {e}") # Log the error for debugging
            user_request_url = settings.BASE_URL # Fallback if URL reverse fails

        user_context = {
            'user_name': user_name,
            'request_obj': request_obj, # Pass the full object to user template for dynamic fields
            'request_url': user_request_url,
            # 'request_id': request_obj.pk,
            # 'request_type': request_obj.request_type_slug.replace('_', ' ').title(),
            # 'request_subject': request_obj.subject,
            # 'request_description': request_obj.description, # Include description
            # Add other details relevant to the user's confirmation email

            # 'request_id', 'request_type', 'request_subject', 'request_description'
            # are now accessible via request_obj in the template if you change it
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
    # Need to define ADMIN_EMAIL_FOR_NOTIFICATIONS in the settings.py
    admin_recipient_email = getattr(settings, 'ADMIN_EMAIL_FOR_NOTIFICATIONS', None)
    if admin_recipient_email:
        # Link to the admin dashboard detail view
        try:
            admin_request_url = settings.BASE_URL + reverse(
                'support_dashboard:request_detail',
                kwargs={'request_type': request_obj.request_type_slug, 'pk': request_obj.pk}
            )
            logger.info(f"Generated admin URL for request {request_obj.pk}: {admin_request_url}")
        except Exception as e:
            logger.error(f"Error reversing support_dashboard request URL for request {request_obj.pk}: {e}")
            admin_request_url = settings.BASE_URL + '/support-dashboard/' # Fallback if URL reverse fails

        admin_context = {
            'request': request_obj,  
            'site_name': getattr(settings, 'SITE_NAME', ''), 
            'admin_request_url': admin_request_url,
        }
        admin_subject = f"New {request_obj.request_type_slug.replace('_', ' ').title()} Submitted: #{request_obj.pk} - {request_obj.subject}"

        # Ensure this template path is correct for the admin email
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