# unified_requests/urls.py
from django.urls import path
from .views import UnifiedRequestSubmitView, SuccessPageView

app_name = 'unified_requests'

urlpatterns = [
    path('submit/', UnifiedRequestSubmitView.as_view(), name='submit_request'),
    path('submit/success/<str:request_type>/<int:pk>/', SuccessPageView.as_view(), name='success_page'),
]