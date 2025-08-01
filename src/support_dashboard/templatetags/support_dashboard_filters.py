from django import template

register = template.Library()

@register.filter
def replace_chars(value, arg):
    """
    Replaces all occurrences of a substring with another substring.
    Usage: {{ value|replace_chars:"old_char:new_char" }}
    Example: {{ "hello_world"|replace_chars:"_: " }}  -> "hello world"
    """
    if not isinstance(value, str):
        return value
    
    try:
        old_char, new_char = arg.split(':')
    except ValueError:
        # Handle cases where arg is not in 'old:new' format
        return value 
    
    return value.replace(old_char, new_char)