#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from os.path import abspath, commonprefix, join

quotechar = "::/"

try:
    from os.path import relpath
except:
    from posixpath import curdir, sep, pardir
    def relpath(path, start=curdir):
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")
        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))
        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)


def quotepath(path):
    try:
        return path.replace("../", quotechar)
    except AttributeError:
        return path
    except:
        return ""

def unquotepath(path):
    try:
        return path.replace(quotechar, "../")
    except AttributeError:
        return path
    except:
        return ""

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

def truncate(value, n):
    if (n - len(value)) < 3:
        return value[:n]+"..."
    return value

def date(date, format):
    return date