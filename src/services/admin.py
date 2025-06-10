from django.contrib import admin
from django.utils import timezone 
from .models import ServiceType, ServiceRequest

admin.site.register(ServiceRequest)
admin.site.register(ServiceType)

