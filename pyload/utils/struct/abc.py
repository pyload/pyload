# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import super

from future import standard_library
standard_library.install_aliases()

__all__ = ['Singleton']


class Singleton(type):
    """
    A metaclass that creates a Singleton base class when called.
    """
    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._inst[cls]
