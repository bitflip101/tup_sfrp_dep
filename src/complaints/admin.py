from django.contrib import admin
from .models import ComplaintCategory, Complaint

admin.site.register(Complaint)
admin.site.register(ComplaintCategory)