from django.contrib import admin
from .models import Inquiry, InquiryCategory


admin.site.register(Inquiry)
admin.site.register(InquiryCategory)
