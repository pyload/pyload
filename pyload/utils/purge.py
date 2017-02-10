# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import re
from builtins import bytes

from future import standard_library

from pyload.utils import convert
from pyload.utils.decorator import iterate

standard_library.install_aliases()


##########################################################################
#: Functions  ############################################################
##########################################################################

@iterate
def chars(value, chars):
    return re.sub(r'[{}]+'.format(chars), '', value)


@iterate
def pattern(value, rules):
    for rule in rules:
        try:
            pattr, repl, flags = rule
        except ValueError:
            pattr, repl = rule
            flags = 0
        value = re.sub(pattr, repl, value, flags)

    return value


@iterate
def replace(value, old, new, count=None):
    return value.replace(old, new, count)


@iterate
def strip(value, chars=None):
    return value.strip(chars)


@iterate
def truncate(name, length):
    max_trunc = len(name) // 2
    if length > max_trunc:
        raise ValueError("File name too short")
    trunc = (len(name) - length) // 3
    return "{}~{}".format(name[:trunc * 2], name[-trunc:])


def uniqify(seq):
    """
    Remove duplicates from list preserving order.
    """
    seen = set()
    seen_add = seen.add
    return type(seq)(x for x in seq if x not in seen and not seen_add(x))


##########################################################################
#: Decorators  ###########################################################
##########################################################################

def args(func):
    from pyload.utils.web import purge as webpurge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str) or isinstance(x, bytes)
        args = convert.convert(args, rule, func=webpurge.text)
        return func(*args, **kwargs)
    return new


def kwargs(func):
    from pyload.utils.web import purge as webpurge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str) or isinstance(x, bytes)
        kwgs = convert.convert(kwargs, rule, func=webpurge.text)
        return func(*args, **kwgs)
    return new
