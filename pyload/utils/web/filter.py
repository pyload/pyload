# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os

from future import standard_library

standard_library.install_aliases()

try:
    from os.path import relpath

except Exception:
    from posixpath import curdir, sep, pardir

    def relpath(path, start=curdir):
        """
        Return a relative version of a path.
        """
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


QUOTECHAR = "::/"


def date(date, format):
    return date


def path_make_absolute(path):
    p = os.path.abspath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def path_make_relative(path):
    p = relpath(path)
    if p[-1] == os.path.sep:
        return p
    else:
        return p + os.path.sep


def quotepath(path):
    try:
        return path.replace("../", QUOTECHAR)
    except AttributeError:
        return path
    except Exception:
        return ""


def truncate(value, n):
    if (n - len(value)) < 3:
        return value[:n] + "..."
    return value


def unquotepath(path):
    try:
        return path.replace(QUOTECHAR, "../")
    except AttributeError:
        return path
    except Exception:
        return ""
