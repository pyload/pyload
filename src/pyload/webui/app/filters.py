# -*- coding: utf-8 -*-

import datetime
import os

from pyload.core.utils import format
from urllib.parse import quote_plus as _quote_plus, unquote_plus as _unquote_plus

_QUOTECHAR = "::%2F"


def quotepath(path):
    try:
        return path.replace(".." + os.path.sep, _QUOTECHAR)
    except AttributeError:
        return path
    except Exception:
        return ""


def unquotepath(path):
    try:
        return path.replace(_QUOTECHAR, ".." + os.path.sep)
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


def quote_plus(arg):
    return _quote_plus(arg)


def unquote_plus(arg):
    return _unquote_plus(arg)


def nbsp(arg):
    return "&nbsp;".join(arg.split(' '))


TEMPLATE_FILTERS = [quotepath, unquotepath, date, relpath, abspath, formatsize, quote_plus, unquote_plus, nbsp]
