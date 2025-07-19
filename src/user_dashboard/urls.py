from django.urls import path
from . import views

# --- ADD THESE TWO PRINT STATEMENTS ---
print(f"DEBUG: Type of views.ProfileSettingsView: {type(views.ProfileSettingsView)}")
print(f"DEBUG: Is views.ProfileSettingsView a class? {isinstance(views.ProfileSettingsView, type)}")
# ------------------------------------

app_name = 'user_dashboard'

urlpatterns = [
    path('', views.user_request_list, name='user_request_list'),
    path('<str:request_type_slug>/<int:pk>/', views.user_request_detail, name='user_request_detail'),
    path('profile-settings/', views.ProfileSettingsView.as_view(), name='profile_settings'),
]