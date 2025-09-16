from django import template

register = template.Library()

@register.filter(name='make_list')
def make_list(value):
    """
    Convierte una cadena de texto en una lista de sus caracteres.
    Ejemplo: "0123456789" -> ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    """
    return list(str(value))

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter para acceder a items de diccionario con claves dinámicas.
    Permite usar variables como claves en plantillas Django.
    """
    if isinstance(dictionary, dict):
        # Intentar primero como entero, luego como string
        try:
            return dictionary.get(int(key), dictionary.get(str(key)))
        except (ValueError, TypeError):
            return dictionary.get(str(key))
    return None
