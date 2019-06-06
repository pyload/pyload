# -*- coding: utf-8 -*-
# AUTHOR: vuolter

from collections.abc import Mapping, MutableMapping


class Singleton(type):
    """A metaclass that creates a Singleton base class when called."""

    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._inst[cls]


class InscDict(MutableMapping):
    """Improved version of the header dictionary from
    `requests.structures.CaseInsensitiveDict`."""

    def __init__(self, *args, **kwargs):
        super(InscDict, self).__init__(*args, **kwargs)

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
        return f"<InscDict {self.__dict__}>"

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            raise TypeError
        # Compare insensitively
        return self.loweritems() == InscDict(other).loweritems()

    def lowerkeys(self):
        """Like `keys`, but with all lowercase keys."""
        return self.__dict__.keys()

    def loweritems(self):
        """Like `items`, but with all lowercase keys."""
        return ((lowerkey, val) for lowerkey, (key, val) in self.__dict__.items())

    def copy(self):
        return InscDict(self.__dict__.values())


class HeaderDict(InscDict):

    __slots__ = []

    def __setitem__(self, key, value):
        InscDict.__setitem__(self, key, value.split(","))

    def __str__(self):
        return f"<Header {self.__dict__}>"

    def list(self):
        """Converts all entries to header list usable by curl."""
        header = []
        for key, val in self.__dict__.values():
            fields = ",".join(val)
            if fields:
                header.append(f"{key}: {fields}")
            else:
                # NOTE: curl will remove this header
                header.append(f"{key}:")
        return header
