# -*- coding: utf-8 -*-

import datetime
import os

from pyload.core.utils import format

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


# NOTE: recheck
def date(text, format):
    return datetime.datetime.strptime(text, format).strftime(format)


#: Use formatsize directly in 0.6.x
def formatsize(*args, **kwargs):
    return format.size(*args, **kwargs)


TEMPLATE_FILTERS = [quotepath, unquotepath, date, relpath, abspath, formatsize]
