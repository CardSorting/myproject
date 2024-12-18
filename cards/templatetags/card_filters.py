from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    return value.split(delimiter)

@register.filter
def trim(value):
    return value.strip()

@register.filter
def startswith(value, prefix):
    return value.startswith(prefix)

@register.filter
def replace(value, arg):
    old, new = arg.split(',')
    return value.replace(old, new)