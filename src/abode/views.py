from django.shortcuts import render

def index(request):
    template_name = "abode/sfrp_landingpage.html"
    context = {}
    return render(request, template_name, context)

def about(request):
    template_name = "abode/sfrp_about.html"
    return render(request, template_name)