# unified_requests/urls.py
from django.urls import path
from .views import UnifiedRequestSubmitView

app_name = 'unified_requests'

urlpatterns = [
    path('submit/', UnifiedRequestSubmitView.as_view(), name='submit_request'),
]