# apps/siaf_sincro/templatetags/almacen_tags.py
from django import template

register = template.Library()

@register.filter(name='tiene_rol')
def tiene_rol(user, group_name):
    """
    Filtro personalizado para plantillas de Django.
    Retorna True si el usuario pertenece al grupo especificado O si es Superusuario (TI).
    Uso en HTML: {% if request.user|tiene_rol:"Nombre_Del_Grupo" %}
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()
