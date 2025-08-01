# faqs/models.py

from django.db import models
from taggit.managers import TaggableManager # Import TaggableManager

class FAQCategory(models.Model):
    """
    Represents a category for FAQ items (e.g., Complaint, Services, Inquiry, Emergency).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the FAQ category (e.g., Complaint, Services)")
    order = models.IntegerField(default=0, help_text="Order in which categories should appear (lower number first)")

    class Meta:
        verbose_name = "FAQ Category"
        verbose_name_plural = "FAQ Categories"
        ordering = ['order', 'name'] # Order categories by 'order' then alphabetically by 'name'

    def __str__(self):
        return self.name

class FAQItem(models.Model):
    """
    Represents a single FAQ question and its answer.
    """
    category = models.ForeignKey(
        FAQCategory,
        on_delete=models.CASCADE, # If a category is deleted, all its FAQ items are also deleted
        related_name='faq_items', # Allows accessing FAQ items from a category object (e.g., category.faq_items.all())
        help_text="The category this FAQ item belongs to"
    )
    question = models.CharField(max_length=255, help_text="The frequently asked question")
    answer = models.TextField(help_text="The detailed answer to the question")
    is_published = models.BooleanField(default=True, help_text="Whether this FAQ item should be visible on the website")
    order = models.IntegerField(default=0, help_text="Order in which FAQ items should appear within their category (lower number first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = TaggableManager(blank=True, help_text="A comma-separated list of tags for this FAQ item.") # NEW: Add tags field


    class Meta:
        verbose_name = "FAQ Item"
        verbose_name_plural = "FAQ Items"
        ordering = ['category__order', 'category__name', 'order', 'question'] # Order by category, then item order, then question
        unique_together = ('category', 'question') # Ensures unique questions within a category

    def __str__(self):
        return f"{self.category.name}: {self.question}"

