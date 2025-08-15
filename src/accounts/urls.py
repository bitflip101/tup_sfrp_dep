from django.urls import path
from django.contrib.auth import views as auth_views # Django's built-in auth views
from . import views # Your custom views
# from .forms import CustomAuthenticationForm # Your custom login form

app_name = "accounts"

urlpatterns = [
    # path('register/', views.register, name='register'),

    # Login view using Django's built-in LoginView with your custom form
    # path('login2/', auth_views.LoginView.as_view(
    #     template_name='accounts/login.html',
    #     authentication_form=CustomAuthenticationForm # Specify your custom login form
    # ), name='login'),

     # Logout view using Django's built-in LogoutView
    # path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'), # Redirects to login after logout

    # path('profile/', views.profile, name='profile'),

    # Homepage URL (must match LOGIN_REDIRECT_URL and register redirect)
    # path('', views.home_page, name='home'),
]