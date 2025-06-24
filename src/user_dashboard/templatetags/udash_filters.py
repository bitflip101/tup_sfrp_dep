from django import template 

register = template.Library()

@register.filter
def replace_chars(value, arg):

    if not isinstance(value, str):
        return value
    if not isinstance(arg, str) or "," not in arg:
        return value # Invalid argument format
    
    old_char, new_char = arg.split(',', 1) # Split by first comma only
    return value.replace(old_char, new_char)