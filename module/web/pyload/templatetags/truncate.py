from django.template.defaultfilters import stringfilter
from django import template

register = template.Library()


@stringfilter
def truncate(value, n):
    if (n - len(value)) < 3:
        return value[:n]+"..."
    return value

register.filter(truncate)
