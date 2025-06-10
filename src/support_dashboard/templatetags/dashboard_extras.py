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