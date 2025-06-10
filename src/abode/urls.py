from django.urls import path
from .views import *

app_name = 'abode'

urlpatterns = [
    path("", index, name="sfrp_lp"),
    path("submit-thanks", submit_thanks, name="submit_thanks"),
    path("about", about, name="sfrp_about"),
    path("privacy_policy", privacy_policy, name="privacy_policy"),
]