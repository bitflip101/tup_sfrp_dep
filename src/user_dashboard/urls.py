from django.urls import path
from . import views

app_name = 'user_dashboard'

urlpatterns = [
    path('', views.user_request_list, name='user_request_list'),
    path('<str:request_type_slug>/<int:pk>/', views.user_request_detail, name='user_request_detail'),
]