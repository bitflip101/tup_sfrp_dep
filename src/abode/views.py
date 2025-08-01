from django.shortcuts import render

def index(request):
    template_name = "abode/sfrp_landingpage.html"
    context = {}
    return render(request, template_name, context)

def submit_thanks(request):
    template_name="abode/sfrp_submit_thankyou.html"
    return render(request, template_name)

def about(request):
    template_name = "abode/sfrp_about.html"
    return render(request, template_name)

def privacy_policy(request):
    template_name = "abode/privacy_policy.html"
    return render(request, template_name)