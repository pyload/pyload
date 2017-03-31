# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library
standard_library.install_aliases()

from ..layer.legacy.collections_ import Mapping, MutableMapping


__all__ = ['HeaderDict', 'InscDict']


class InscDict(MutableMapping):
    """
    Improved version of the header dictionary from `requests.structures.CaseInsensitiveDict`.
    """
    __slots__ = ['__dict__']

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        return self.__dict__[key.lower()][-1]

    def __setitem__(self, key, value):
        # NOTE: Use the lowercased key for lookups, but store the actual key
        # alongside the value
        self.__dict__[key.lower()] = (key, value)

    def __delitem__(self, key):
        del self.__dict__[key.lower()]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(key for key, val in self.__dict__.values())

    def __str__(self):
        return """<InscDict {0}>""".format(self.__dict__)

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplementedError
        #: Compare insensitively
        return self._loweritems() == InscDict(other)._loweritems()

    def _loweritems(self):
        """
        Like `items`, but with all lowercase keys.
        """
        return ((lowerkey, val)
                for lowerkey, (key, val) in self.__dict__.items())

    def copy(self):
        return InscDict(self.__dict__.values())


class HeaderDict(InscDict):

    __slots__ = []

    def __setitem__(self, key, value):
        InscDict.__setitem__(self, key, value.split(','))

    def __str__(self):
        return """<Header {0}>""".format(self.__dict__)

    def list(self):
        """
        Converts all entries to header list usable by curl.
        """
        header = []
        for key, val in self.__dict__.values():
            fields = ','.join(val)
            if fields:
                header.append("{0}: {1}".format(key, fields))
            else:
                # NOTE: curl will remove this header
                header.append("{0}:".format(key))
        return header
