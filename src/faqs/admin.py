# faqs/admin.py

from django.contrib import admin
from .models import FAQCategory, FAQItem

@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for FAQCategory model.
    """
    list_display = ('name', 'order')
    search_fields = ('name',)
    list_editable = ('order',) # Allows editing order directly from the list view

@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for FAQItem model.
    """
    list_display = ('question', 'category', 'is_published', 'order', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer')
    list_editable = ('is_published', 'order') # Allows editing published status and order directly
    raw_id_fields = ('category',) # Useful for many categories, shows ID instead of dropdown
    date_hierarchy = 'created_at' # Adds date drill-down navigation

    # Method to display tags in the list view
    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = "Tags"