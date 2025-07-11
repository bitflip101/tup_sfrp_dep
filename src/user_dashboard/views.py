# user_dashboard/views.py
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required 
from django.core.paginator import Paginator 
from django.db.models import Q # For Search

# Import request models
from complaints.models import Complaint 
from services.models import ServiceRequest 
from inquiries.models import Inquiry 
from emergencies.models import EmergencyReport 

# For attachments
from django.contrib.contenttypes.models import ContentType
from attachments.models import RequestAttachment # Import the RequestAttachment model

@login_required
def user_request_list(request):
    template_name = "user_dashboard/user_request_list.html"
    user = request.user
    all_user_requests = []

    # Query requests from each model submitted by the current user.
    complaints = Complaint.objects.filter(submitted_by=user).select_related('category')
    service_requests = ServiceRequest.objects.filter(submitted_by=user).select_related('service_type')
    inquiries = Inquiry.objects.filter(submitted_by=user).select_related('category')
    emergencies = EmergencyReport.objects.filter(submitted_by=user).select_related('emergency_type')

    # Combine and standardize common fields for display
    for req in complaints:
        all_user_requests.append({
            'pk': req.pk,
            'request_type_slug': 'complaint',
            'subject': req.subject,
            'description': req.description, 
            'status': req.status,
            'submitted_at': req.submitted_at,
            'display_type': 'Complaint',
            'specific_field': req.category.name if hasattr(req, 'category') and req.category else 'N/A',
            'full_object': req, # 
        })

    for req in service_requests:
        all_user_requests.append({
            'pk': req.pk,
            'request_type_slug': 'service_request',
            'subject': req.subject,
            'description': req.description,
            'status': req.status,
            'submitted_at': req.submitted_at,
            'display_type': 'Service Request',
            'specific_field': req.service_type.name if hasattr(req, 'service_type') and req.service_type else 'N/A',
            'full_object': req,
        })
    
    for req in inquiries:
        all_user_requests.append({
            'pk': req.pk,
            'request_type_slug': 'inquiry',
            'subject': req.subject, # Or req.question, adjust as per your model
            'description': req.description, # Or req.question
            'status': req.status,
            'submitted_at': req.submitted_at,
            'display_type': 'Inquiry',
            'specific_field': req.category.name if hasattr(req, 'category') and req.category else 'N/A',
            'full_object': req,
        })

    for req in emergencies:
        all_user_requests.append({
            'pk': req.pk,
            'request_type_slug': 'emergency',
            'subject': req.subject,
            'description': req.description,
            'status': req.status,
            'submitted_at': req.submitted_at,
            'display_type': 'Emergency Report',
            'specific_field': req.emergency_type.name if hasattr(req, 'emergency_type') and req.emergency_type else 'N/A',
            'full_object': req,
        })

    # Sort the combined list by submitted date (newest first)
    all_user_requests.sort(key=lambda x: x['submitted_at'], reverse=True)

    # --- Filtering and Seach ----
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        all_user_requests = [req for req in all_user_requests if req['status'] == status_filter]
    
    type_filter = request.GET.get('type')
    if type_filter and type_filter != 'all':
        all_user_requests = [req for req in all_user_requests if req['request_type_slug'] == type_filter]
    
    search_query = request.GET.get('q')
    if search_query:
        search_query_lower = search_query.lower()
        all_user_requests = [
            req for req in all_user_requests
            if search_query_lower in req['subject'].lower() or search_query_lower in req['description'].lower() or search_query_lower in req['display_type'.lower()]
        ]

    # --- Pagination ---
    paginator = Paginator(all_user_requests, 10) # Show 10 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_query': search_query,
        'status_choices': [('new', 'New'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed'), ('rejected', 'Rejected')],
        'request_type_choices': [('complaint', 'Complaint'), ('service_request', 'Service Request'), ('inquiry', 'Inquiry'), ('emergency', 'Emergency Report')]
    }

    return render(request, template_name, context)

@login_required
def user_request_detail(request, request_type_slug, pk):
    template_name = "user_dashboard/user_request_detail.html"
    user = request.user
    print(user) # Keep for debugging if needed

    request_obj = None
    
    # Dynamically determine the model based on request_type_slug
    if request_type_slug == 'complaint':
        model = Complaint
    elif request_type_slug == 'service_request':
        model = ServiceRequest
    elif request_type_slug == 'inquiry':
        model = Inquiry
    elif request_type_slug == 'emergency':
        model = EmergencyReport
    else:
        # If an invalid slug is provided raise 404
        raise Http404("Invalid request type.")

    # Get specific object, ensuring it belongs to the current user
    # This also acts as a security check
    request_obj = get_object_or_404(model, pk=pk, submitted_by=user)

    # --- Fetch Attachments for this request ---
    attachments = []
    if request_obj:
        content_type = ContentType.objects.get_for_model(request_obj.__class__)
        attachments = RequestAttachment.objects.filter(
            content_type=content_type,
            object_id=request_obj.pk
        )

    context = {
        'request_obj': request_obj,
        'request_type_slug': request_type_slug, # Pass slug for potential use in template
        'attachments': attachments, # Add attachments to the context
    }

    return render(request, template_name, context)
