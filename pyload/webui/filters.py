# -*- coding: utf-8 -*-

import os

quotechar = "::/"

try:
    from os.path import relpath
except Exception:
    from posixpath import curdir, sep, pardir


    def os.relpath(path, start=curdir):
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")
        start_list = os.path.abspath(start).split(sep)
        path_list = os.path.abspath(path).split(sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))
        rel_list = [pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return curdir
        return os.path.join(*rel_list)


def quotepath(path):
    try:
        return path.replace("../", quotechar)
    except AttributeError:
        return path
    except Exception:
        return ""


def unquotepath(path):
    try:
        return path.replace(quotechar, "../")
    except AttributeError:
        return path
    except Exception:
        return ""


def path_make_absolute(path):
    p = os.path.abspath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def path_make_relative(path):
    p = os.relpath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def truncate(value, n):
    if (n - len(value)) < 3:
        return value[:n] + "..."
    return value


def date(date, format):
    return date
