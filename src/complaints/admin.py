from django.contrib import admin
from django.utils import timezone
from .models import ComplaintCategory, Complaint, ComplaintUpdate

# --- NEW: Custom List Filter for Anonymous Submissions ---
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'subject',
        'category',
        'status',         # Display status in list view
        'assigned_to',    # Display assigned person in list view
        'submitted_by',
        'submitted_at',
        'priority',
    )
    list_filter = (
        'status',         # Allow filtering by status
        'category',
        'priority',
        'assigned_to',    # Allow filtering by assigned person
        'submitted_at',
    )
    search_fields = (
        'subject',
        'description',
        'location_address',
        'submitted_by__email', # Search by submitter's email
        'full_name', # Search by anonymous name
        'email',     # Search by anonymous email
    )
    # Fields to show and their order in the detail view
    fieldsets = (
        ('Request Details', {
            'fields': ('request_type', 'subject', 'description', 'category', 'priority', 'location_address', 'latitude', 'longitude')
        }),
        ('Submission Info', {
            'fields': ('submitted_by', 'full_name', 'email', 'phone_number', 'submitted_at'),
            'classes': ('collapse',), # Optionally collapse this section
        }),
        ('Management', {
            'fields': ('status', 'assigned_to', 'updated_at') # Add new fields here
        }),
    )
    # Make the 'status' and 'assigned_to' fields editable directly from the list view
    list_editable = ('status', 'assigned_to')
    # Display submitted_at and updated_at as read-only
    readonly_fields = ('submitted_at', 'updated_at')

    def get_fieldsets(self, request, obj=None):
        # Dynamic fieldsets to exclude 'request_type' when not needed for Complaint
        fieldsets = super().get_fieldsets(request, obj)
        for fs in fieldsets:
            if 'Request Details' in fs[0]:
                # Remove 'request_type' if it's there (it's a form field, not model field)
                if 'request_type' in fs[1]['fields']:
                    fs[1]['fields'] = tuple(f for f in fs[1]['fields'] if f != 'request_type')
        return fieldsets

@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
