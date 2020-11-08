# -*- coding: utf-8 -*-

import datetime
import os

from pyload.core.utils import format

_QUOTECHAR = "::"
_ESCAPED_SLASH = "%2F"


def quotepath(path):
    try:
        return path.replace("..", _QUOTECHAR).replace("/", _ESCAPED_SLASH)
    except AttributeError:
        return path
    except Exception:
        return ""


def unquotepath(path):
    try:
        return path.replace(_QUOTECHAR, "..").replace(_ESCAPED_SLASH, "/")
    except AttributeError:
        return path
    except Exception:
        return ""


def abspath(path):
    p = os.path.abspath(path)
    if os.path.isfile(p):
        return p
    elif p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def relpath(path):
    p = os.path.relpath(path)
    if os.path.isfile(p):
        return p
    elif p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def date(date, format):
    return datetime.datetime.strftime(date, format)


#: Use formatsize directly in 0.6.x
def formatsize(*args, **kwargs):
    return format.size(*args, **kwargs)


TEMPLATE_FILTERS = [quotepath, unquotepath, date, relpath, abspath, formatsize]
