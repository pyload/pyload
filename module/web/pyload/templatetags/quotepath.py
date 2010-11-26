import os
from posixpath import curdir, sep, pardir, join

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

def relpath(path, start=curdir):
    """Return a relative version of a path"""
    if not path:
        raise ValueError("no path specified")
    start_list = posixpath.abspath(start).split(sep)
    path_list = posixpath.abspath(path).split(sep)
    # Work out how much of the filepath is shared by start and path.
    i = len(posixpath.commonprefix([start_list, path_list]))
    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)

register.filter(path_make_relative)

