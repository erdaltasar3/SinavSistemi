from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Dictionary içinden bir değer almak için kullanılan özel filtre
    Kullanım: {{ dict|get_item:key }}
    """
    return dictionary.get(key) 