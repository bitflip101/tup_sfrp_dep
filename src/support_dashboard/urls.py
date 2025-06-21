# support_dashboard/urls.py
from django.urls import path
from .views import RequestListView, RequestDetailView, RequestTrendView

app_name = 'support_dashboard' # Important for namespacing

urlpatterns = [
    path('', RequestListView.as_view(), name='request_list'),
    path('<str:request_type>/<int:pk>/', RequestDetailView.as_view(), name='request_detail'),
    path('request-trend/', RequestTrendView.as_view(), name='request-trend'),

]