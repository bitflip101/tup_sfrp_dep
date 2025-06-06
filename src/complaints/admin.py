from django.contrib import admin
from django.utils import timezone
from .models import ComplaintCategory, Complaint, ComplaintUpdate

# --- NEW: Custom List Filter for Anonymous Submissions ---
class AnonymousSubmissionFilter(admin.SimpleListFilter):
    title = 'Anonymous Submission' # Human-readable title for the filter
    parameter_name = 'is_anonymous' # URL parameter name

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each tuple is the coded value
        for the option that will appear in the URL query. The second element is the
        human-readable name for the option that will appear in the right sidebar.
        """
        return [
            ('yes', 'Yes'),
            ('no', 'No'),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string.
        """
        if self.value() == 'yes':
            # Anonymous if submitted_by is NULL
            # You might want to refine this based on your property's exact logic
            # e.g., submitted_by__isnull=True AND (full_name__isnull=False OR email__isnull=False)
            return queryset.filter(submitted_by__isnull=True)
        if self.value() == 'no':
            # Not anonymous if submitted_by is NOT NULL
            return queryset.filter(submitted_by__isnull=False)
        return queryset # Return the original queryset if no filter is applied

# --- ComplaintCategory Admin (no change needed here for this issue) ---
@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# --- ComplaintUpdate Inline (no change needed here for this issue) ---
class ComplaintUpdateInline(admin.TabularInline):
    model = ComplaintUpdate
    extra = 0
    fields = (
        'update_type', 
        'message', 
        'is_public', 
        'old_status', 
        'new_status', 
        'old_priority', 
        'new_priority', 
        'old_assigned_to', 
        'new_assigned_to', 
        'updated_by', 
        'created_at'
    )
    readonly_fields = (
        'created_at', 
        'updated_by',
        'old_status', 
        'new_status', 
        'old_priority', 
        'new_priority', 
        'old_assigned_to', 
        'new_assigned_to'
    )

# --- Complaint Admin (Updated list_filter) ---
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'subject', 
        'submitted_by', 
        'category', 
        'status', 
        'priority', 
        'assigned_to', 
        'created_at'
    )
    
    # IMPORTANT: Use the new custom filter here!
    list_filter = (
        'status', 
        'priority', 
        'category', 
        'created_at', 
        'assigned_to', 
        AnonymousSubmissionFilter, # Use your custom filter class here
    )
    
    search_fields = (
        'subject',        
        'description', 
        'full_name',      
        'email',          
        'submitted_by__email', 
        'submitted_by__username'
    )
    
    raw_id_fields = ('submitted_by', 'assigned_to')
    inlines = [ComplaintUpdateInline]
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_closed']

    def mark_as_resolved(self, request, queryset):
        updated_count = queryset.update(status='resolved', resolved_at=timezone.now())
        for complaint in queryset:
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                message=f"Complaint marked as resolved via admin action.",
                update_type='resolution',
                old_status=complaint.status,
                new_status='resolved'
            )
        self.message_user(request, f"{updated_count} complaints marked as resolved.")
    mark_as_resolved.short_description = "Mark selected complaints as Resolved"

    def mark_as_in_progress(self, request, queryset):
        updated_count = queryset.update(status='in_progress')
        for complaint in queryset:
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                message=f"Complaint marked as in progress via admin action.",
                update_type='status_change',
                old_status=complaint.status,
                new_status='in_progress'
            )
        self.message_user(request, f"{updated_count} complaints marked as In Progress.")
    mark_as_in_progress.short_description = "Mark selected complaints as In Progress"

    def mark_as_closed(self, request, queryset):
        updated_count = queryset.update(status='closed')
        for complaint in queryset:
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                message=f"Complaint marked as closed via admin action.",
                update_type='status_change',
                old_status=complaint.status,
                new_status='closed'
            )
        self.message_user(request, f"{updated_count} complaints marked as Closed.")
    mark_as_closed.short_description = "Mark selected complaints as Closed"

# --- ComplaintUpdate Admin (no change needed here for this issue) ---
@admin.register(ComplaintUpdate)
class ComplaintUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'complaint', 
        'update_type', 
        'message', 
        'is_public', 
        'updated_by', 
        'created_at', 
        'old_status', 'new_status', 
        'old_priority', 'new_priority', 
        'old_assigned_to', 'new_assigned_to'
    )
    
    list_filter = (
        'is_public', 
        'update_type', 
        'created_at', 
        'old_status', 
        'new_status', 
        'old_priority', 
        'new_priority'
    )
    
    search_fields = (
        'complaint__subject', 
        'message', 
        'updated_by__email', 
        'updated_by__username',
        'old_status', 'new_status'
    )
    raw_id_fields = ('complaint', 'updated_by', 'old_assigned_to', 'new_assigned_to')
    fieldsets = (
        (None, {
            'fields': ('complaint', 'updated_by', 'message', 'is_public', 'update_type')
        }),
        ('Change Details', {
            'fields': (
                ('old_status', 'new_status'),
                ('old_priority', 'new_priority'),
                ('old_assigned_to', 'new_assigned_to'),
            ),
            'description': 'These fields capture specific changes made by the update.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'updated_by', 
        'old_status', 
        'new_status', 
        'old_priority', 
        'new_priority', 
        'old_assigned_to', 
        'new_assigned_to'
    )