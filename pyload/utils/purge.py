# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

import re
from builtins import bytes

from future import standard_library

from pyload.utils import convert

from .decorator import iterate

standard_library.install_aliases()


__all__ = ['args', 'chars', 'kwargs', 'pattern', 'truncate', 'uniqify']


##########################################################################
#: Functions  ############################################################
##########################################################################

@iterate
def chars(s, chars, repl=''):
    return re.sub(r'[{}]+'.format(chars), repl, s)


@iterate
def pattern(s, rules):
    for rule in rules:
        try:
            pattr, repl, flags = rule
        except ValueError:
            pattr, repl = rule
            flags = 0
        s = re.sub(pattr, repl, s, flags)
    return s


def truncate(s, offset):
    max_trunc = len(s) // 2
    if offset > max_trunc:
        raise ValueError("String too short")
    trunc = (len(s) - offset) // 3
    return "{}~{}".format(s[:trunc * 2], s[-trunc:])


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
    from .web import purge as webpurge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str) or isinstance(x, bytes)
        args = convert.convert(args, rule, func=webpurge.text)
        return func(*args, **kwargs)
    return new


def kwargs(func):
    from .web import purge as webpurge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str) or isinstance(x, bytes)
        kwgs = convert.convert(kwargs, rule, func=webpurge.text)
        return func(*args, **kwgs)
    return new
