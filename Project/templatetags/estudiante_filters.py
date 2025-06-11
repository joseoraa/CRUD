# tu_app/templatetags/estudiante_filters.py

from django import template
from ..models import Nota

register = template.Library()

@register.filter
def get_notas(estudiante):
    try:
        return Nota.objects.get(inscripcion=estudiante)
    except Nota.DoesNotExist:
        return None



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

