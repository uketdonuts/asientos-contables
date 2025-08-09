from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter para acceder a items de diccionario con claves dinámicas"""
    try:
        return dictionary.get(int(key), {})
    except (ValueError, AttributeError):
        return {}
