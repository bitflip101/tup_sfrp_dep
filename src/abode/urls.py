from django.urls import path
from .views import *

app_name = 'abode'

urlpatterns = [
    path("", index, name="sfrp_lp"),
    path("about", about, name="sfrp_about"),
]