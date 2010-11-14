from django.template.defaultfilters import stringfilter
from django import template

register = template.Library()

quotechar = "::/"

@stringfilter
def quotepath(path):
    try:
        return path.replace("../", quotechar)
    except AttributeError:
        return path
    except:
        return ""


register.filter(quotepath)

@stringfilter
def unquotepath(path):
    try:
        return path.replace(quotechar, "../")
    except AttributeError:
        return path
    except:
        return ""

register.filter(unquotepath)