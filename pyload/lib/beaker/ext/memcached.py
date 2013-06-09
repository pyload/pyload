from beaker.container import NamespaceManager, Container
from beaker.exceptions import InvalidCacheBackendError, MissingCacheParameter
from beaker.synchronization import file_synchronizer, null_synchronizer
from beaker.util import verify_directory, SyncDict
import warnings

memcache = None

class MemcachedNamespaceManager(NamespaceManager):
    clients = SyncDict()
    
    @classmethod
    def _init_dependencies(cls):
        global memcache
        if memcache is not None:
            return
        try:
            import pylibmc as memcache
        except ImportError:
            try:
                import cmemcache as memcache
                warnings.warn("cmemcache is known to have serious "
                            "concurrency issues; consider using 'memcache' or 'pylibmc'")
            except ImportError:
                try:
                    import memcache
                except ImportError:
                    raise InvalidCacheBackendError("Memcached cache backend requires either "
                                                        "the 'memcache' or 'cmemcache' library")
        
    def __init__(self, namespace, url=None, data_dir=None, lock_dir=None, **params):
        NamespaceManager.__init__(self, namespace)
       
        if not url:
            raise MissingCacheParameter("url is required") 
        
        if lock_dir:
            self.lock_dir = lock_dir
        elif data_dir:
            self.lock_dir = data_dir + "/container_mcd_lock"
        if self.lock_dir:
            verify_directory(self.lock_dir)            
        
        self.mc = MemcachedNamespaceManager.clients.get(url, memcache.Client, url.split(';'))

    def get_creation_lock(self, key):
        return file_synchronizer(
            identifier="memcachedcontainer/funclock/%s" % self.namespace,lock_dir = self.lock_dir)

    def _format_key(self, key):
        return self.namespace + '_' + key.replace(' ', '\302\267')

    def __getitem__(self, key):
        return self.mc.get(self._format_key(key))

    def __contains__(self, key):
        value = self.mc.get(self._format_key(key))
        return value is not None

    def has_key(self, key):
        return key in self

    def set_value(self, key, value, expiretime=None):
        if expiretime:
            self.mc.set(self._format_key(key), value, time=expiretime)
        else:
            self.mc.set(self._format_key(key), value)

    def __setitem__(self, key, value):
        self.set_value(key, value)
        
    def __delitem__(self, key):
        self.mc.delete(self._format_key(key))

    def do_remove(self):
        self.mc.flush_all()
    
    def keys(self):
        raise NotImplementedError("Memcache caching does not support iteration of all cache keys")

class MemcachedContainer(Container):
    namespace_class = MemcachedNamespaceManager
