from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def send_complaint_notification_emails(complaint_instance):
    """
    Sends email notifications to the user who submitted the complaint and to the admin.
    """
    # Define your site's domain for URL construction (adjust if using specific site config)
    # For local development, this might be '127.0.0.1:8000'
    # For production, it should be your actual domain (e.g., 'www.yourwebsite.com')
    # You might get this from Django's Sites framework if you've configured it.
    site_domain = '127.0.0.1:8000' # Make this dynamic in production settings or use Sites framework

    # --- Email to User (Submitter) ---
    user_email = None
    user_name = "Valued User"

    if complaint_instance.submitted_by:
        user_email = complaint_instance.submitted_by.email
        user_name = complaint_instance.submitted_by.get_full_name() or complaint_instance.submitted_by.username
    elif complaint_instance.email: # For anonymous complaints
        user_email = complaint_instance.email
        user_name = complaint_instance.full_name or "Anonymous User"

    # Ensure DEFAULT_FROM_EMAIL is set
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')
    if not from_email:
        logger.error("DEFAULT_FROM_EMAIL is not set in settings. Emails cannot be sent.")
        return # Exit the function if no sender email
    
     # Try sending email to user
    if user_email:
        try:
            # Validate user_email format if necessary, though send_mail might catch it
            if not user_email.strip(): # Basic check for empty string
                logger.warning(f"User email is empty for complaint #{complaint_instance.id}. Skipping user notification.")
            else:
                user_subject = f"Your Complaint #{complaint_instance.id} Has Been Submitted"
                complaint_url = f"http://{site_domain}{reverse('complaints:user_complaint_detail', args=[complaint_instance.id])}"

                user_context = {
                    'user_name': user_name,
                    'complaint': complaint_instance,
                    'complaint_url': complaint_url,
                    'site_name': getattr(settings, 'PROJECT_NAME', 'Our Platform'),
                }
                
                # Try rendering email template for user
                try:
                    html_message_user = render_to_string('notifications/complaint_submitted_user_email.html', user_context)
                    plain_message_user = strip_tags(html_message_user)
                except Exception as e:
                    logger.error(f"Error rendering user email template for complaint #{complaint_instance.id}: {e}", exc_info=True)
                    html_message_user = None # Ensure it's not used if rendering failed
                    plain_message_user = f"Error rendering email. Your complaint ID: {complaint_instance.id}"

                if html_message_user: # Only attempt to send if template rendered successfully
                    send_mail(
                        user_subject,
                        plain_message_user,
                        from_email,
                        [user_email],
                        html_message=html_message_user,
                        fail_silently=False,
                    )
                    logger.info(f"SIMULATED EMAIL SENT to user: {user_email} for Complaint #{complaint_instance.id}")
                else:
                    logger.warning(f"Skipping user email send due to rendering error for complaint #{complaint_instance.id}.")

        except Exception as e:
            logger.error(f"Failed to send user email for complaint #{complaint_instance.id} to {user_email}: {e}", exc_info=True)
    else:
        logger.info(f"No user email found for complaint #{complaint_instance.id}. Skipping user notification.")


    # --- Email to Admin ---
    admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]
    if not admin_emails:
        logger.warning("No ADMINS defined in settings.py. Skipping admin complaint notification.")
        # Optional: set a fallback admin email for development if you don't want to define ADMINS
        # admin_emails = ['admin@example.com'] 
    
    if admin_emails:
        try:
            admin_subject = f"New Complaint Submitted: #{complaint_instance.id} - {complaint_instance.subject}"
            admin_complaint_url = f"http://{site_domain}/admin/complaints/complaint/{complaint_instance.id}/change/"

            admin_context = {
                'complaint': complaint_instance,
                'admin_complaint_url': admin_complaint_url,
                'site_name': getattr(settings, 'PROJECT_NAME', 'Our Platform'),
            }
            
            # Try rendering email template for admin
            try:
                html_message_admin = render_to_string('notifications/complaint_submitted_admin_email.html', admin_context)
                plain_message_admin = strip_tags(html_message_admin)
            except Exception as e:
                logger.error(f"Error rendering admin email template for complaint #{complaint_instance.id}: {e}", exc_info=True)
                html_message_admin = None
                plain_message_admin = f"Error rendering email. New complaint ID: {complaint_instance.id}"

            if html_message_admin: # Only attempt to send if template rendered successfully
                send_mail(
                    admin_subject,
                    plain_message_admin,
                    from_email,
                    admin_emails,
                    html_message=html_message_admin,
                    fail_silently=False,
                )
                logger.info(f"SIMULATED EMAIL SENT to admins: {', '.join(admin_emails)} for Complaint #{complaint_instance.id}")
            else:
                logger.warning(f"Skipping admin email send due to rendering error for complaint #{complaint_instance.id}.")

        except Exception as e:
            logger.error(f"Failed to send admin email for complaint #{complaint_instance.id}: {e}", exc_info=True)
    else:
        logger.info(f"No admin emails configured. Skipping admin notification for complaint #{complaint_instance.id}.")