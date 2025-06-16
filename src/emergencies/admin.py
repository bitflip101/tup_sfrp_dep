from django.contrib import admin
from .models import EmergencyReport, EmergencyType

admin.site.register(EmergencyReport)
admin.site.register(EmergencyType)