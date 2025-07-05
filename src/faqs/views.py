# faqs/views.py

from django.shortcuts import render
from .models import FAQCategory, FAQItem

def faq_list(request):
    """
    Renders the FAQ page, displaying categories and their associated FAQ items.
    Categories and items are ordered as defined in their models.
    Only published FAQ items are displayed.
    Includes print statements for debugging.
    """
    print("\n--- Debugging FAQ List View ---")

    # Get all FAQ categories, ordered as specified in the model's Meta class
    categories = FAQCategory.objects.all()
    # print(f"Fetched {categories.count()} categories:")
    # for cat in categories:
    #     print(f"- Category ID: {cat.id}, Name: {cat.name}, Order: {cat.order}")

    # Create a dictionary to hold categories and their published FAQ items
    categorized_faqs = {}
    for category in categories:
        # Get all published FAQ items for the current category, ordered as specified
        items = FAQItem.objects.filter(category=category, is_published=True).order_by('order', 'question')
        
        # print(f"  Checking category '{category.name}': Found {items.count()} published items.")
        
        if items.exists(): # Only include categories that have published items
            categorized_faqs[category] = items
            # print(f"  Category '{category.name}' added to categorized_faqs.")
        else:
            print(f"  Category '{category.name}' has no published items, skipping.")

    # print(f"Final categorized_faqs contains {len(categorized_faqs)} categories.")
    # for cat_obj, item_queryset in categorized_faqs.items():
        # print(f"- Category '{cat_obj.name}' has {item_queryset.count()} items.")

    context = {
        'categorized_faqs': categorized_faqs,
        'page_title': 'Frequently Asked Questions', # Title for the page
    }
    # print("--- End Debugging FAQ List View ---\n")
    return render(request, 'faqs/faqs_list.html', context)