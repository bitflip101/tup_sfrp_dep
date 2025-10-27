from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('abode.urls')),

    path('accounts/', include('allauth.urls')),

    # Keeping the custom accounts URLs for profile, etc.,..update - profile now is in user_dashboard app (TODO: Cleanup this accounts app)
    # but allauth handles register, login, logout, password reset, email verification
    path('accounts/', include("accounts.urls")),

    path('requests/', include("unified_requests.urls")),
    path('support-dashboard/', include("support_dashboard.urls")),
    path('user-dashboard/', include('user_dashboard.urls')),

    # FAQS
    path('faqs/', include('faqs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)