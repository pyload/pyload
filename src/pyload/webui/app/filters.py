# -*- coding: utf-8 -*-


import os

quotechar = "::%2F"

def quotepath(path):
    try:
        return path.replace(".." + os.path.sep, quotechar)
    except AttributeError:
        return path
    except Exception:
        return ""


def unquotepath(path):
    try:
        return path.replace(quotechar, ".." + os.path.sep)
    except AttributeError:
        return path
    except Exception:
        return ""


def path_make_absolute(path):
    p = os.path.abspath(path)
    if os.path.isfile(p):
        return p
    elif p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def path_make_relative(path):
    p = os.path.relpath(path)
    if os.path.isfile(p):
        return p
    elif p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def truncate(value, n):
    if (n - len(value)) < 3:
        return value[:n] + "..."
    return value


def date(date, format):
    return date
