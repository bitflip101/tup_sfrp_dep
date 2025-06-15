# services/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy 
from django.db import transaction
from django.utils import timezone 

from .models import ServiceRequest, ServiceType
# from .forms import 