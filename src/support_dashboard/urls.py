# support_dashboard/urls.py
from django.urls import path
from .views import (
    RequestListView, RequestDetailView,
    # Importing the category management views
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
     # Importing the new user management views
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    # Import the new group management views
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView,
    # FAQS
    FAQCategoryListView, FAQCategoryCreateView, FAQCategoryUpdateView, FAQCategoryDeleteView,
    FAQItemListView, FAQItemCreateView, FAQItemUpdateView, FAQItemDeleteView,
)

app_name = 'support_dashboard'

urlpatterns = [
    # --- Request Management URLs ---
    path('', RequestListView.as_view(), name='request_list'),
    path('<str:request_type>/<int:pk>/', RequestDetailView.as_view(), name='request_detail'),
    # path('request-trend/', RequestTrendView.as_view(), name='request-trend'),

    # --- Category Management URLs ---
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


    # --- User Management URLs ---
    # {% url 'support_dashboard:user_list' %}
    
    # List all users
    path('users/', UserListView.as_view(), name='user_list'),

    # Create a new user
    path('users/add/', UserCreateView.as_view(), name='user_create'),

    # Update an existing user
    # The 'user_pk' corresponds to pk_url_kwarg in UserUpdateView
    path('users/<int:user_pk>/edit/', UserUpdateView.as_view(), name='user_update'),

    # Delete an existing user
    # The 'user_pk' corresponds to pk_url_kwarg in UserDeleteView
    path('users/<int:user_pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    # --- Group Management URLs ---
    # Example usage in template:
    # {% url 'support_dashboard:group_list' %}

    # List all groups
    path('groups/', GroupListView.as_view(), name='group_list'),

    # Create a new group
    path('groups/add/', GroupCreateView.as_view(), name='group_create'),

    # Update an existing group
    # The 'group_pk' corresponds to pk_url_kwarg in GroupUpdateView
    path('groups/<int:group_pk>/edit/', GroupUpdateView.as_view(), name='group_update'),

    # Delete an existing group
    # The 'group_pk' corresponds to pk_url_kwarg in GroupDeleteView
    path('groups/<int:group_pk>/delete/', GroupDeleteView.as_view(), name='group_delete'),# --- NEW: FAQ Management URLs ---
    # FAQ Category Management
    path('faqs/categories/', FAQCategoryListView.as_view(), name='faq_category_list'),
    path('faqs/categories/add/', FAQCategoryCreateView.as_view(), name='faq_category_create'),
    path('faqs/categories/<int:pk>/edit/', FAQCategoryUpdateView.as_view(), name='faq_category_update'),
    path('faqs/categories/<int:pk>/delete/', FAQCategoryDeleteView.as_view(), name='faq_category_delete'),

    # FAQ Item Management
    path('faqs/items/', FAQItemListView.as_view(), name='faq_item_list'),
    path('faqs/items/add/', FAQItemCreateView.as_view(), name='faq_item_create'),
    path('faqs/items/<int:pk>/edit/', FAQItemUpdateView.as_view(), name='faq_item_update'),
    path('faqs/items/<int:pk>/delete/', FAQItemDeleteView.as_view(), name='faq_item_delete'),


]
