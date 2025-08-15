from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login
# from .forms import CustomUserCreationForm # Import your custom registration form

# View for user registration
# def register(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user) # Log the user in immediately after successful registration
#             return redirect('home') # Redirect to the 'home' page
#     else:
#         form = CustomUserCreationForm()
#     return render(request, 'accounts/register.html', {'form': form})


# def login(request):
#     context = {}
#     template_name = "accounts/login.html"
#     return render(request, template_name, context)

# def profile(request):
#     context = {}
#     template_name = "accounts/profile.html"
#     return render(request, template_name, context)

# def logout(request):
#     context = {}
#     template_name = "accounts/logout.html"
#     return render(request, template_name, context)


# def home_page(request):
#     return render(request, 'accounts/home.html')

