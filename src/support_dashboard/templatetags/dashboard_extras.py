from django import template

register = template.Library()

@register.filter(name='instance_of')
def instance_of(obj, class_name):
    return obj.__class__.__name__ == class_name

@register.filter(name='split') # Add this filter too for cleaner path splitting
def split_string(value, key):
    """
    Splits a string by the given key.
    Useful for splitting file paths to get the filename.
    """
    return value.split(key)[-1]

@register.filter # NEW: Add this replace filter
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another string.
    Usage: {{ value|replace:"old_string,new_string" }}
    For our case: {{ req.request_type_slug|title|replace:'_',' ' }}
    """
    if not isinstance(value, str) or not isinstance(arg, str) or ',' not in arg:
        return value # Return original value if inputs are not as expected
    
    old_char, new_char = arg.split(',', 1)
    return value.replace(old_char, new_char)