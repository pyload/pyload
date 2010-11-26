import os

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

def path_make_absolute(path):
    p = os.path.abspath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


register.filter(path_make_absolute)

def path_make_relative(path):
    p = os.path.relpath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep

register.filter(path_make_relative)

