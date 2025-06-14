from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = 'http://127.0.0.1:8000' # Change to actual domain in production!

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-p74f_ejx5#vl#3f0u@^8r27*12@snvnukd6edc)0lf)por-he#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # custom
    'abode',
    'accounts',
    'complaints',
    'services',
    'inquiries',
    'emergencies',
    'unified_requests',
    'notifications',
    'attachments',
    'support_dashboard',

    # allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount', # Optional, if you plan to add social logins later
    'django.contrib.sites', # Required by allauth
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIR = [
    os.path.join(BASE_DIR, 'static/'), 
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom User Model Settings ---
AUTH_USER_MODEL = 'accounts.CustomUser' # Tells Django to use your custom user model

# URL to redirect to after successful login
LOGIN_REDIRECT_URL = 'home' # Use 'home' as the name of your homepage URL

# URL to redirect to after logout (optional)
LOGOUT_REDIRECT_URL = 'login' # Redirect back to the login page

# --- Allauth Specific Settings ---
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter' # Path to your custom adapter

# This LOGIN_REDIRECT_URL will be overridden by the adapter's logic for logged-in users.
# It primarily serves as a fallback for Django's default login if not using allauth,
# or for some allauth edge cases where the adapter might not be called.
# You can set it to a general user page.
LOGIN_REDIRECT_URL = '/requests/submit/' # Or your general user post-login pages

# Required for allauth to function
SITE_ID = 1

# Authentication Backends
# This ensures allauth's authentication backend is used alongside Django's default.
# It's crucial for allauth to correctly handle email-based authentication etc.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # Django's default authentication backend (for admin, etc.)
    'allauth.account.auth_backends.AuthenticationBackend', # allauth specific authentication methods
]

# Allauth General Account Settings
# ACCOUNT_AUTHENTICATION_METHOD = 'email' # Users log in with their email address
ACCOUNT_LOGIN_METHODS = {'email'}
# ACCOUNT_EMAIL_REQUIRED = True         # Email is required for registration
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True           # Email addresses must be unique
# ACCOUNT_USERNAME_REQUIRED = False     # Username is NOT required (since we use email for login)
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
# ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True # User has to enter password twice on signup
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_SESSION_REMEMBER = True       # "Remember me" option on login
ACCOUNT_EMAIL_VERIFICATION = 'mandatory' # Email verification is mandatory
# ACCOUNT_EMAIL_VERIFICATION = 'optional' # For optional email verification
# ACCOUNT_EMAIL_VERIFICATION = 'none' # For no email verification

# ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5 # Optional: Lock account after 5 failed attempts
# ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300 # Optional: Lockout for 5 minutes (300 seconds)
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m', # 5 attempts per 5 minutes
    # You can add other rate limits here as needed, e.g.:
    # 'email_confirmation': '5/h', # 5 email confirmations per hour
    # 'password_reset': '3/h', # 3 password resets per hour
}

# Custom User Model (keep this as you already have CustomUser)
AUTH_USER_MODEL = 'accounts.CustomUser'

# Redirect URLs after certain actions (use reverse_lazy for URLs that aren't evaluated until needed)
LOGIN_REDIRECT_URL = '/requests/submit/' # After successful login, redirect to unified submit page
# Or use reverse_lazy if you include 'unified_requests' app_name in your project urls.py
# LOGIN_REDIRECT_URL = reverse_lazy('unified_requests:submit_request')

ACCOUNT_LOGOUT_REDIRECT_URL = '/' # After logout, redirect to home page
# ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3 # Optional: How many days until verification link expires (default is 3)

# --- Email Configuration for LOCAL DEVELOPMENT ---
# When testing locally without an SMTP server:

## - FOR DEVELOPMENT - Email Notification Simulation
# Option 1: This will print emails to your console (terminal) instead of sending them.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Option 2: Write emails to files
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails') # Make sure this directory exists or is created

# - FOR PRODUCTION: Configure your actual email service (e.g., SendGrid, Mailgun, Gmail SMTP)
#-Email settings for allauth (re-using your existing email config)
#-Ensure these are correctly set for sending emails
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' # Or ConsoleBackend for dev
# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your_smtp_username'
# EMAIL_HOST_PASSWORD = 'your_smtp_password'
# DEFAULT_FROM_EMAIL = 'no-reply@yourinstitution.com'
# SERVER_EMAIL = 'admin@yourinstitution.com' # For error reports etc.


DEFAULT_FROM_EMAIL = 'noreply@tup.sfrp.edu.ph'
SERVER_EMAIL = 'noreply@tup.sfrp.edu.ph' # Used for error emails by Django

## Email address for receiving new request alerts for custom notifications
ADMIN_EMAIL_FOR_NOTIFICATIONS = 'SFRP_Admi@tup.sfrp.edu.ph' # Use the same email address as in ADMINS if it's the primary alert email

## - RECEIPIENTS FOR EMAIL NOTIFICATIONS, FOR USER AND ADMIN ALERTS
ADMINS = [
    ('SFRP Admin', 'sfrpAdmin@tup.sfrp.edu.ph'),
    # Add more admin emails as needed
]

PROJECT_NAME = "SFRP-TUP HelpLine"

# Media files (for user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')