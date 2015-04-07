"""Container and Namespace classes"""
import anydbm
import cPickle
import logging
import os
import time

import beaker.util as util
from beaker.exceptions import CreationAbortedError, MissingCacheParameter
from beaker.synchronization import _threading, file_synchronizer, \
     mutex_synchronizer, NameLock, null_synchronizer

__all__ = ['Value', 'Container', 'ContainerContext',
           'MemoryContainer', 'DBMContainer', 'NamespaceManager',
           'MemoryNamespaceManager', 'DBMNamespaceManager', 'FileContainer',
           'OpenResourceNamespaceManager',
           'FileNamespaceManager', 'CreationAbortedError']


logger = logging.getLogger('beaker.container')
if logger.isEnabledFor(logging.DEBUG):
    debug = logger.debug
else:
    def debug(message, *args):
        pass


class NamespaceManager(object):
    """Handles dictionary operations and locking for a namespace of
    values.
    
    The implementation for setting and retrieving the namespace data is
    handled by subclasses.
    
    NamespaceManager may be used alone, or may be privately accessed by
    one or more Container objects.  Container objects provide per-key
    services like expiration times and automatic recreation of values.
    
    Multiple NamespaceManagers created with a particular name will all
    share access to the same underlying datasource and will attempt to
    synchronize against a common mutex object.  The scope of this
    sharing may be within a single process or across multiple
    processes, depending on the type of NamespaceManager used.
    
    The NamespaceManager itself is generally threadsafe, except in the
    case of the DBMNamespaceManager in conjunction with the gdbm dbm
    implementation.

    """
    
    @classmethod
    def _init_dependencies(cls):
        pass
        
    def __init__(self, namespace):
        self._init_dependencies()
        self.namespace = namespace
        
    def get_creation_lock(self, key):
        raise NotImplementedError()

    def do_remove(self):
        raise NotImplementedError()

    def acquire_read_lock(self):
        pass

    def release_read_lock(self):
        pass

    def acquire_write_lock(self, wait=True):
        return True

    def release_write_lock(self):
        pass

    def has_key(self, key):
        return self.__contains__(key)

    def __getitem__(self, key):
        raise NotImplementedError()
        
    def __setitem__(self, key, value):
        raise NotImplementedError()
    
    def set_value(self, key, value, expiretime=None):
        """Optional set_value() method called by Value.
        
        Allows an expiretime to be passed, for namespace
        implementations which can prune their collections
        using expiretime.
        
        """
        self[key] = value
        
    def __contains__(self, key):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()
    
    def keys(self):
        raise NotImplementedError()
    
    def remove(self):
        self.do_remove()
        

class OpenResourceNamespaceManager(NamespaceManager):
    """A NamespaceManager where read/write operations require opening/
    closing of a resource which is possibly mutexed.
    
    """
    def __init__(self, namespace):
        NamespaceManager.__init__(self, namespace)
        self.access_lock = self.get_access_lock()
        self.openers = 0
        self.mutex = _threading.Lock()

    def get_access_lock(self):
        raise NotImplementedError()

    def do_open(self, flags): 
        raise NotImplementedError()

    def do_close(self): 
        raise NotImplementedError()

    def acquire_read_lock(self): 
        self.access_lock.acquire_read_lock()
        try:
            self.open('r', checkcount = True)
        except:
            self.access_lock.release_read_lock()
            raise
            
    def release_read_lock(self):
        try:
            self.close(checkcount = True)
        finally:
            self.access_lock.release_read_lock()
        
    def acquire_write_lock(self, wait=True): 
        r = self.access_lock.acquire_write_lock(wait)
        try:
            if (wait or r): 
                self.open('c', checkcount = True)
            return r
        except:
            self.access_lock.release_write_lock()
            raise
            
    def release_write_lock(self): 
        try:
            self.close(checkcount=True)
        finally:
            self.access_lock.release_write_lock()

    def open(self, flags, checkcount=False):
        self.mutex.acquire()
        try:
            if checkcount:
                if self.openers == 0: 
                    self.do_open(flags)
                self.openers += 1
            else:
                self.do_open(flags)
                self.openers = 1
        finally:
            self.mutex.release()

    def close(self, checkcount=False):
        self.mutex.acquire()
        try:
            if checkcount:
                self.openers -= 1
                if self.openers == 0: 
                    self.do_close()
            else:
                if self.openers > 0:
                    self.do_close()
                self.openers = 0
        finally:
            self.mutex.release()

    def remove(self):
        self.access_lock.acquire_write_lock()
        try:
            self.close(checkcount=False)
            self.do_remove()
        finally:
            self.access_lock.release_write_lock()

class Value(object):
    __slots__ = 'key', 'createfunc', 'expiretime', 'expire_argument', 'starttime', 'storedtime',\
                'namespace'

    def __init__(self, key, namespace, createfunc=None, expiretime=None, starttime=None):
        self.key = key
        self.createfunc = createfunc
        self.expire_argument = expiretime
        self.starttime = starttime
        self.storedtime = -1
        self.namespace = namespace

    def has_value(self):
        """return true if the container has a value stored.

        This is regardless of it being expired or not.

        """
        self.namespace.acquire_read_lock()
        try:    
            return self.namespace.has_key(self.key)
        finally:
            self.namespace.release_read_lock()

    def can_have_value(self):
        return self.has_current_value() or self.createfunc is not None  

    def has_current_value(self):
        self.namespace.acquire_read_lock()
        try:    
            has_value = self.namespace.has_key(self.key)
            if has_value:
                try:
                    stored, expired, value = self._get_value()
                    return not self._is_expired(stored, expired)
                except KeyError:
                    pass
            return False
        finally:
            self.namespace.release_read_lock()

    def _is_expired(self, storedtime, expiretime):
        """Return true if this container's value is expired."""
        return (
            (
                self.starttime is not None and
                storedtime < self.starttime
            )
            or
            (
                expiretime is not None and
                time.time() >= expiretime + storedtime
            )
        )

    def get_value(self):
        self.namespace.acquire_read_lock()
        try:
            has_value = self.has_value()
            if has_value:
                try:
                    stored, expired, value = self._get_value()
                    if not self._is_expired(stored, expired):
                        return value
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    has_value = False
                    
            if not self.createfunc:
                raise KeyError(self.key)
        finally:
            self.namespace.release_read_lock()

        has_createlock = False
        creation_lock = self.namespace.get_creation_lock(self.key)
        if has_value:
            if not creation_lock.acquire(wait=False):
                debug("get_value returning old value while new one is created")
                return value
            else:
                debug("lock_creatfunc (didnt wait)")
                has_createlock = True

        if not has_createlock:
            debug("lock_createfunc (waiting)")
            creation_lock.acquire()
            debug("lock_createfunc (waited)")

        try:
            # see if someone created the value already
            self.namespace.acquire_read_lock()
            try:
                if self.has_value():
                    try:
                        stored, expired, value = self._get_value()
                        if not self._is_expired(stored, expired):
                            return value
                    except KeyError:
                        # guard against un-mutexed backends raising KeyError
                        pass
            finally:
                self.namespace.release_read_lock()

            debug("get_value creating new value")
            v = self.createfunc()
            self.set_value(v)
            return v
        finally:
            creation_lock.release()
            debug("released create lock")

    def _get_value(self):
        value = self.namespace[self.key]
        try:
            stored, expired, value = value
        except ValueError:
            if not len(value) == 2:
                raise
            # Old format: upgrade
            stored, value = value
            expired = self.expire_argument
            debug("get_value upgrading time %r expire time %r", stored, self.expire_argument)
            self.namespace.release_read_lock()
            self.set_value(value, stored)
            self.namespace.acquire_read_lock()
        except TypeError:
            # occurs when the value is None.  memcached 
            # may yank the rug from under us in which case 
            # that's the result
            raise KeyError(self.key)            
        return stored, expired, value

    def set_value(self, value, storedtime=None):
        self.namespace.acquire_write_lock()
        try:
            if storedtime is None:
                storedtime = time.time()
            debug("set_value stored time %r expire time %r", storedtime, self.expire_argument)
            self.namespace.set_value(self.key, (storedtime, self.expire_argument, value))
        finally:
            self.namespace.release_write_lock()

    def clear_value(self):
        self.namespace.acquire_write_lock()
        try:
            debug("clear_value")
            if self.namespace.has_key(self.key):
                try:
                    del self.namespace[self.key]
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    pass
            self.storedtime = -1
        finally:
            self.namespace.release_write_lock()

class AbstractDictionaryNSManager(NamespaceManager):
    """A subclassable NamespaceManager that places data in a dictionary.
    
    Subclasses should provide a "dictionary" attribute or descriptor
    which returns a dict-like object.   The dictionary will store keys
    that are local to the "namespace" attribute of this manager, so
    ensure that the dictionary will not be used by any other namespace.

    e.g.::
    
        import collections
        cached_data = collections.defaultdict(dict)
        
        class MyDictionaryManager(AbstractDictionaryNSManager):
            def __init__(self, namespace):
                AbstractDictionaryNSManager.__init__(self, namespace)
                self.dictionary = cached_data[self.namespace]
                
    The above stores data in a global dictionary called "cached_data",
    which is structured as a dictionary of dictionaries, keyed
    first on namespace name to a sub-dictionary, then on actual
    cache key to value.
    
    """
    
    def get_creation_lock(self, key):
        return NameLock(
            identifier="memorynamespace/funclock/%s/%s" % (self.namespace, key),
            reentrant=True
        )

    def __getitem__(self, key): 
        return self.dictionary[key]

    def __contains__(self, key): 
        return self.dictionary.__contains__(key)

    def has_key(self, key): 
        return self.dictionary.__contains__(key)
        
    def __setitem__(self, key, value):
        self.dictionary[key] = value
    
    def __delitem__(self, key):
        del self.dictionary[key]

    def do_remove(self):
        self.dictionary.clear()
        
    def keys(self):
        return self.dictionary.keys()
    
class MemoryNamespaceManager(AbstractDictionaryNSManager):
    namespaces = util.SyncDict()

    def __init__(self, namespace, **kwargs):
        AbstractDictionaryNSManager.__init__(self, namespace)
        self.dictionary = MemoryNamespaceManager.namespaces.get(self.namespace,
                                                                dict)

class DBMNamespaceManager(OpenResourceNamespaceManager):
    def __init__(self, namespace, dbmmodule=None, data_dir=None, 
            dbm_dir=None, lock_dir=None, digest_filenames=True, **kwargs):
        self.digest_filenames = digest_filenames
        
        if not dbm_dir and not data_dir:
            raise MissingCacheParameter("data_dir or dbm_dir is required")
        elif dbm_dir:
            self.dbm_dir = dbm_dir
        else:
            self.dbm_dir = data_dir + "/container_dbm"
        util.verify_directory(self.dbm_dir)
        
        if not lock_dir and not data_dir:
            raise MissingCacheParameter("data_dir or lock_dir is required")
        elif lock_dir:
            self.lock_dir = lock_dir
        else:
            self.lock_dir = data_dir + "/container_dbm_lock"
        util.verify_directory(self.lock_dir)

        self.dbmmodule = dbmmodule or anydbm

        self.dbm = None
        OpenResourceNamespaceManager.__init__(self, namespace)

        self.file = util.encoded_path(root= self.dbm_dir,
                                      identifiers=[self.namespace],
                                      extension='.dbm',
                                      digest_filenames=self.digest_filenames)
        
        debug("data file %s", self.file)
        self._checkfile()

    def get_access_lock(self):
        return file_synchronizer(identifier=self.namespace,
                                 lock_dir=self.lock_dir)
                                 
    def get_creation_lock(self, key):
        return file_synchronizer(
                    identifier = "dbmcontainer/funclock/%s" % self.namespace, 
                    lock_dir=self.lock_dir
                )

    def file_exists(self, file):
        if os.access(file, os.F_OK): 
            return True
        else:
            for ext in ('db', 'dat', 'pag', 'dir'):
                if os.access(file + os.extsep + ext, os.F_OK):
                    return True
                    
        return False
    
    def _checkfile(self):
        if not self.file_exists(self.file):
            g = self.dbmmodule.open(self.file, 'c') 
            g.close()
                
    def get_filenames(self):
        list = []
        if os.access(self.file, os.F_OK):
            list.append(self.file)
            
        for ext in ('pag', 'dir', 'db', 'dat'):
            if os.access(self.file + os.extsep + ext, os.F_OK):
                list.append(self.file + os.extsep + ext)
        return list

    def do_open(self, flags):
        debug("opening dbm file %s", self.file)
        try:
            self.dbm = self.dbmmodule.open(self.file, flags)
        except:
            self._checkfile()
            self.dbm = self.dbmmodule.open(self.file, flags)

    def do_close(self):
        if self.dbm is not None:
            debug("closing dbm file %s", self.file)
            self.dbm.close()
        
    def do_remove(self):
        for f in self.get_filenames():
            os.remove(f)
        
    def __getitem__(self, key): 
        return cPickle.loads(self.dbm[key])

    def __contains__(self, key): 
        return self.dbm.has_key(key)
        
    def __setitem__(self, key, value):
        self.dbm[key] = cPickle.dumps(value)

    def __delitem__(self, key):
        del self.dbm[key]

    def keys(self):
        return self.dbm.keys()


class FileNamespaceManager(OpenResourceNamespaceManager):
    def __init__(self, namespace, data_dir=None, file_dir=None, lock_dir=None,
                 digest_filenames=True, **kwargs):
        self.digest_filenames = digest_filenames
        
        if not file_dir and not data_dir:
            raise MissingCacheParameter("data_dir or file_dir is required")
        elif file_dir:
            self.file_dir = file_dir
        else:
            self.file_dir = data_dir + "/container_file"
        util.verify_directory(self.file_dir)

        if not lock_dir and not data_dir:
            raise MissingCacheParameter("data_dir or lock_dir is required")
        elif lock_dir:
            self.lock_dir = lock_dir
        else:
            self.lock_dir = data_dir + "/container_file_lock"
        util.verify_directory(self.lock_dir)
        OpenResourceNamespaceManager.__init__(self, namespace)

        self.file = util.encoded_path(root=self.file_dir, 
                                      identifiers=[self.namespace],
                                      extension='.cache',
                                      digest_filenames=self.digest_filenames)
        self.hash = {}
        
        debug("data file %s", self.file)

    def get_access_lock(self):
        return file_synchronizer(identifier=self.namespace,
                                 lock_dir=self.lock_dir)
                                 
    def get_creation_lock(self, key):
        return file_synchronizer(
                identifier = "filecontainer/funclock/%s" % self.namespace, 
                lock_dir = self.lock_dir
                )
        
    def file_exists(self, file):
        return os.access(file, os.F_OK)

    def do_open(self, flags):
        if self.file_exists(self.file):
            fh = open(self.file, 'rb')
            try:
                self.hash = cPickle.load(fh)
            except (IOError, OSError, EOFError, cPickle.PickleError, ValueError):
                pass
            fh.close()

        self.flags = flags
        
    def do_close(self):
        if self.flags == 'c' or self.flags == 'w':
            fh = open(self.file, 'wb')
            cPickle.dump(self.hash, fh)
            fh.close()

        self.hash = {}
        self.flags = None
                
    def do_remove(self):
        try:
            os.remove(self.file)
        except OSError, err:
            # for instance, because we haven't yet used this cache,
            # but client code has asked for a clear() operation...
            pass
        self.hash = {}
        
    def __getitem__(self, key): 
        return self.hash[key]

    def __contains__(self, key): 
        return self.hash.has_key(key)
        
    def __setitem__(self, key, value):
        self.hash[key] = value

    def __delitem__(self, key):
        del self.hash[key]

    def keys(self):
        return self.hash.keys()


#### legacy stuff to support the old "Container" class interface

namespace_classes = {}

ContainerContext = dict
    
class ContainerMeta(type):
    def __init__(cls, classname, bases, dict_):
        namespace_classes[cls] = cls.namespace_class
        return type.__init__(cls, classname, bases, dict_)
    def __call__(self, key, context, namespace, createfunc=None,
                 expiretime=None, starttime=None, **kwargs):
        if namespace in context:
            ns = context[namespace]
        else:
            nscls = namespace_classes[self]
            context[namespace] = ns = nscls(namespace, **kwargs)
        return Value(key, ns, createfunc=createfunc,
                     expiretime=expiretime, starttime=starttime)

class Container(object):
    __metaclass__ = ContainerMeta
    namespace_class = NamespaceManager

class FileContainer(Container):
    namespace_class = FileNamespaceManager

class MemoryContainer(Container):
    namespace_class = MemoryNamespaceManager

class DBMContainer(Container):
    namespace_class = DBMNamespaceManager

DbmContainer = DBMContainer
