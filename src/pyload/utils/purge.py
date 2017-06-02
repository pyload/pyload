# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import os
import re
import sys
from builtins import bytes

from future import standard_library

from . import convert

standard_library.install_aliases()


##########################################################################
#: Functions  ############################################################
##########################################################################

def chars(text, chars, repl=''):
    return re.sub(r'[{0}]+'.format(chars), repl, text)


__unixbadchars = ('\0', '/', '\\')
__macbadchars = __unixbadchars + (':',)
__winbadchars = __macbadchars + ('<', '>', '"', '|', '?', '*')
__winbadwords = (
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
    'con', 'prn')

def name(text, sep='_', allow_whitespaces=False):
    """
    Remove invalid characters.
    """
    bc = __winbadchars if os.name else __macbadchars if sys.platform else __unixbadchars
    repl = r''.join(bc)
    if not allow_whitespaces:
        repl += ' '
    name = chars(text, repl, sep).strip()
    if os.name == 'nt' and name.lower() in __winbadwords:
        name = sep + name
    return name


def pattern(text, rules):
    for rule in rules:
        try:
            pattr, repl, flags = rule
        except ValueError:
            pattr, repl = rule
            flags = 0
        text = re.sub(pattr, repl, text, flags)
    return text


def truncate(text, offset):
    max_trunc = len(text) // 2
    if offset > max_trunc:
        raise ValueError("String too short")
    trunc = (len(text) - offset) // 3
    return "{0}~{1}".format(text[:trunc * 2], text[-trunc:])


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
    from .web import purge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str)
        args = convert.convert(args, rule, func=purge.text)
        return func(*args, **kwargs)
    return new


def kwargs(func):
    from .web import purge

    def new(*args, **kwargs):
        rule = lambda x: isinstance(x, str) or isinstance(x, bytes)
        kwgs = convert.convert(kwargs, rule, func=purge.text)
        return func(*args, **kwgs)
    return new
