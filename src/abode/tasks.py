from celery import shared_task 
from django.core.mail import send_mail


@shared_task
def send_test_email():
    """"
    Sends a test email to confirm Celery and email backend are working.
    """

    send_mail(
        'TUP SFRP Test Email',
        'This is a test email send from TUP SFRP, thru Celery task!',
        'bigflip.signal@gmail.com',
        ['tolitz09@yahoo.com'],
        fail_silently=False,
    )
    return "Test email sent!"