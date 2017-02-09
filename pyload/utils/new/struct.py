# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

from pyload.utils.new.decorator import lock
from pyload.utils.new.lib.collections import Mapping, MutableMapping
from pyload.utils.new.lib.safe_threading import RLock


##########################################################################
#: Types  ################################################################
##########################################################################

class LockObject(object):

    __slots__ = ('lock')

    def __init__(self):
        self.lock = RLock()

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if name.startswith('_') or not callable(attr):
            return attr

        @lock
        def wrapper(self, *args, **kwargs):
            return attr(*args, **kwargs)
        return wrapper


class Info(MutableMapping):

    class ReadError(KeyError):

        def __str__(self):
            return """<ReadError {}>""".format(self.message)

    class WriteError(KeyError):

        def __str__(self):
            return """<WriteError {}>""".format(self.message)

    class DeleteError(KeyError):

        def __str__(self):
            return """<DeleteError {}>""".format(self.message)

    __readable__ = True
    __writeable__ = True
    __updateable__ = True
    __deleteable__ = True

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __delattr__(self, name):
        try:
            self.__delitem__(name)
        except self.DeleteError:
            raise
        except KeyError:
            pass

    def __getitem__(self, key):
        if not self.readable:
            raise self.ReadError
        return self.__dict__[key]

    def __setitem__(self, key, value):
        if not self.writable or not self.updateable and key not in self.__dict__:
            raise self.WriteError
        self.__dict__[key] = value

    def __delitem__(self, key):
        if not self.deletable:
            raise self.DeleteError
        del self.__dict__[key]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def __str__(self):
        return """<Info {}>""".format(self.__dict__)

    @property
    def readable(self):
        return bool(self.__readable__)

    @property
    def writable(self):
        return bool(self.__writeable__)

    @property
    def updateable(self):
        return bool(self.__updateable__)

    @property
    def deletable(self):
        return bool(self.__deleteable__)

    def lock(self, read=True, write=True, update=False, delete=False):
        self.__readable__ = read
        self.__writeable__ = write
        self.__updateable__ = update
        self.__deleteable__ = delete

    def unlock(self):
        self.__readable__ = True
        self.__writeable__ = True
        self.__updateable__ = True
        self.__deleteable__ = True


class InscDict(MutableMapping):
    """
    Improved version of the header dictionary from `requests.structures.CaseInsensitiveDict`.
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        return self.__dict__[key.lower()][-1]

    def __setitem__(self, key, value):
        # NOTE: Use the lowercased key for lookups, but store the actual key alongside the value
        self.__dict__[key.lower()] = (key, value)

    def __delitem__(self, key):
        del self.__dict__[key.lower()]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(key for key, val in self.__dict__.values())

    def __str__(self):
        return """<InscDict {}>""".format(self.__dict__)

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplementedError
        #: Compare insensitively
        return self._loweritems() == InscDict(other)._loweritems()

    def _loweritems(self):
        """
        Like `items`, but with all lowercase keys.
        """
        return ((lowerkey, val) for lowerkey, (key, val) in self.__dict__.items())

    def copy(self):
        return InscDict(self.__dict__.values())


class InscInfo(InscDict, Info):

    def __getitem__(self, key):
        if not self.readable:
            raise self.ReadError
        return InscDict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if not self.writable or not self.updateable and key.lower() not in self.__dict__:
            raise self.WriteError
        InscDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if not self.deletable:
            raise self.DeleteError
        InscDict.__delitem__(self, key)

    def __str__(self):
        return """<InscInfo {}>""".format(self.__dict__)


# TODO: Move elsewhere...
class SyncInfo(Info):

    __local__ = None  # NOTE: Refer to the internal __dict__ used by <Info> class
    __remote__ = None

    def __init__(self, remotedict, *args, **kwargs):
        Info.__init__(self, *args, **kwargs)
        self.__local__ = self.__dict__
        self.__remote__ = remotedict
        self.sync()

    def __setitem__(self, key, value):
        Info.__setitem__(self, key, value)
        self.__remote__[key] = value

    def __delitem__(self, key):
        Info.__delitem__(self, key)
        del self.__remote__[key]

    def sync(self, reverse=False):
        if reverse:
            self.synclocal()
        else:
            self.syncremote()

    def syncremote(self):
        self.__remote__.update(self.copy())

    def synclocal(self):
        d = {k: v for k, v in self.__remote__.items() if k in self}
        self.update(d)


class HeadDict(InscDict):

    def __setitem__(self, key, value):
        InscDict.__setitem__(self, key, value.split(','))

    def __str__(self):
        return """<Header {}>""".format(self.__dict__)

    def list(self):
        """
        Converts all entries to header list usable by curl.
        """
        header = []
        for key, val in self.__dict__.values():
            fields = ','.join(val)
            if fields:
                header.append("{}: {}".format(key, fields))
            else:
                # NOTE: curl will remove this header
                header.append("{}:".format(key))
        return header
