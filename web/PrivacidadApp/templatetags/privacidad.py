from django import template

from PrivacidadApp.names import author_name as _author_name

register = template.Library()


@register.filter
def author_name(user):
    """«Cuenta eliminada» for erased accounts; full name or username otherwise."""
    return _author_name(user)
