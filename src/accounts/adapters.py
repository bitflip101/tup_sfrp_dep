from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle post-login redirection based on user role.
    """
    def get_login_redirect_url(self, request):
        # Check if the user is staff (admin or support)
        if request.user.is_staff:
            # Redirect staff users to the support dashboard's request list page
            return reverse('support_dashboard:request_list')
        else:
            # Redirect regular users (non-staff) to the unified request submission form
            return reverse('unified_requests:submit_request')