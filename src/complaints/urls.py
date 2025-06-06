from django.urls import path
from .views import (
    ComplaintCreateView,
    UserComplaintListView,
    UserComplaintDetailView,
    AdminComplaintListView,
    AdminComplaintDetailView
)

app_name = 'complaints' # Important for URL namespacing

urlpatterns = [
    # User-facing URLs
    path('submit/', ComplaintCreateView.as_view(), name='submit_complaint'),
    path('my_complaints/', UserComplaintListView.as_view(), name='my_complaints'),
    path('<int:pk>/', UserComplaintDetailView.as_view(), name='user_complaint_detail'),

    # Admin-facing URLs
    path('admin/', AdminComplaintListView.as_view(), name='admin_complaints'),
    path('admin/<int:pk>/', AdminComplaintDetailView.as_view(), name='admin_complaint_detail'),
]