from django import template

register = template.Library()

@register.filter
def replace_chars(value, arg):
    """
    Replaces all occurrences of a substring with another substring.
    Usage: {{ value|replace:"old,new" }}
    Example: {{ "hello world"|replace:"o,X" }}  would output "hellX wXrld"
    """
    if not isinstance(value, str):
        return value

    try:
        old, new = arg.split(',')
    except ValueError:
        return value # Return original value if arg is not in 'old,new' format

    return value.replace(old, new)