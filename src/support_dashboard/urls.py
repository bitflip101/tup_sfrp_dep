# support_dashboard/urls.py
from django.urls import path
from .views import (
    RequestListView, RequestDetailView, RequestTrendView,
    # NEW: Import the new category management views
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView
)

app_name = 'support_dashboard' # Important for namespacing

urlpatterns = [
    # --- Existing Request Management URLs ---
    path('', RequestListView.as_view(), name='request_list'),
    path('<str:request_type>/<int:pk>/', RequestDetailView.as_view(), name='request_detail'),
    path('request-trend/', RequestTrendView.as_view(), name='request-trend'),

    # --- NEW: Category Management URLs ---
    # Example usage in template:
    # {% url 'support_dashboard:category_list' category_type_slug='complaint' %}

    # List all categories of a specific type
    path('categories/<str:category_type_slug>/', CategoryListView.as_view(), name='category_list'),

    # Create a new category of a specific type
    path('categories/<str:category_type_slug>/add/', CategoryCreateView.as_view(), name='category_create'),

    # Update an existing category of a specific type
    # The 'category_pk' corresponds to pk_url_kwarg in CategoryUpdateView
    path('categories/<str:category_type_slug>/<int:category_pk>/edit/', CategoryUpdateView.as_view(), name='category_update'),

    # Delete an existing category of a specific type
    # The 'category_pk' corresponds to pk_url_kwarg in CategoryDeleteView
    path('categories/<str:category_type_slug>/<int:category_pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]
