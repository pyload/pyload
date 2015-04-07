"""Cache object

The Cache object is used to manage a set of cache files and their
associated backend. The backends can be rotated on the fly by
specifying an alternate type when used.

Advanced users can add new backends in beaker.backends

"""
    
import warnings

import beaker.container as container
import beaker.util as util
from beaker.exceptions import BeakerException, InvalidCacheBackendError

import beaker.ext.memcached as memcached
import beaker.ext.database as database
import beaker.ext.sqla as sqla
import beaker.ext.google as google

# Initialize the basic available backends
clsmap = {
          'memory':container.MemoryNamespaceManager,
          'dbm':container.DBMNamespaceManager,
          'file':container.FileNamespaceManager,
          'ext:memcached':memcached.MemcachedNamespaceManager,
          'ext:database':database.DatabaseNamespaceManager,
          'ext:sqla': sqla.SqlaNamespaceManager,
          'ext:google': google.GoogleNamespaceManager,
          }

# Initialize the cache region dict
cache_regions = {}
cache_managers = {}

try:
    import pkg_resources

    # Load up the additional entry point defined backends
    for entry_point in pkg_resources.iter_entry_points('beaker.backends'):
        try:
            NamespaceManager = entry_point.load()
            name = entry_point.name
            if name in clsmap:
                raise BeakerException("NamespaceManager name conflict,'%s' "
                                      "already loaded" % name)
            clsmap[name] = NamespaceManager
        except (InvalidCacheBackendError, SyntaxError):
            # Ignore invalid backends
            pass
        except:
            import sys
            from pkg_resources import DistributionNotFound
            # Warn when there's a problem loading a NamespaceManager
            if not isinstance(sys.exc_info()[1], DistributionNotFound):
                import traceback
                from StringIO import StringIO
                tb = StringIO()
                traceback.print_exc(file=tb)
                warnings.warn("Unable to load NamespaceManager entry point: '%s': "
                              "%s" % (entry_point, tb.getvalue()), RuntimeWarning,
                              2)
except ImportError:
    pass
    



def cache_region(region, *deco_args):
    """Decorate a function to cache itself using a cache region
    
    The region decorator requires arguments if there are more than
    2 of the same named function, in the same module. This is
    because the namespace used for the functions cache is based on
    the functions name and the module.
    
    
    Example::
        
        # Add cache region settings to beaker:
        beaker.cache.cache_regions.update(dict_of_config_region_options))
        
        @cache_region('short_term', 'some_data')
        def populate_things(search_term, limit, offset):
            return load_the_data(search_term, limit, offset)
        
        return load('rabbits', 20, 0)
    
    .. note::
        
        The function being decorated must only be called with
        positional arguments.
    
    """
    cache = [None]
    
    def decorate(func):
        namespace = util.func_namespace(func)
        def cached(*args):
            reg = cache_regions[region]
            if not reg.get('enabled', True):
                return func(*args)
            
            if not cache[0]:
                if region not in cache_regions:
                    raise BeakerException('Cache region not configured: %s' % region)
                cache[0] = Cache._get_cache(namespace, reg)
            
            cache_key = " ".join(map(str, deco_args + args))
            def go():
                return func(*args)
            
            return cache[0].get_value(cache_key, createfunc=go)
        cached._arg_namespace = namespace
        cached._arg_region = region
        return cached
    return decorate


def region_invalidate(namespace, region, *args):
    """Invalidate a cache region namespace or decorated function
    
    This function only invalidates cache spaces created with the
    cache_region decorator.
    
    :param namespace: Either the namespace of the result to invalidate, or the
        cached function reference
    
    :param region: The region the function was cached to. If the function was
        cached to a single region then this argument can be None
    
    :param args: Arguments that were used to differentiate the cached
        function as well as the arguments passed to the decorated
        function

    Example::
        
        # Add cache region settings to beaker:
        beaker.cache.cache_regions.update(dict_of_config_region_options))
        
        def populate_things(invalidate=False):
            
            @cache_region('short_term', 'some_data')
            def load(search_term, limit, offset):
                return load_the_data(search_term, limit, offset)
            
            # If the results should be invalidated first
            if invalidate:
                region_invalidate(load, None, 'some_data',
                                        'rabbits', 20, 0)
            return load('rabbits', 20, 0)
    
    """
    if callable(namespace):
        if not region:
            region = namespace._arg_region
        namespace = namespace._arg_namespace

    if not region:
        raise BeakerException("Region or callable function "
                                    "namespace is required")
    else:
        region = cache_regions[region]
    
    cache = Cache._get_cache(namespace, region)
    cache_key = " ".join(str(x) for x in args)
    cache.remove_value(cache_key)


class Cache(object):
    """Front-end to the containment API implementing a data cache.

    :param namespace: the namespace of this Cache

    :param type: type of cache to use

    :param expire: seconds to keep cached data

    :param expiretime: seconds to keep cached data (legacy support)

    :param starttime: time when cache was cache was
    
    """
    def __init__(self, namespace, type='memory', expiretime=None,
                 starttime=None, expire=None, **nsargs):
        try:
            cls = clsmap[type]
            if isinstance(cls, InvalidCacheBackendError):
                raise cls
        except KeyError:
            raise TypeError("Unknown cache implementation %r" % type)
            
        self.namespace = cls(namespace, **nsargs)
        self.expiretime = expiretime or expire
        self.starttime = starttime
        self.nsargs = nsargs
    
    @classmethod
    def _get_cache(cls, namespace, kw):
        key = namespace + str(kw)
        try:
            return cache_managers[key]
        except KeyError:
            cache_managers[key] = cache = cls(namespace, **kw)
            return cache
        
    def put(self, key, value, **kw):
        self._get_value(key, **kw).set_value(value)
    set_value = put
    
    def get(self, key, **kw):
        """Retrieve a cached value from the container"""
        return self._get_value(key, **kw).get_value()
    get_value = get
    
    def remove_value(self, key, **kw):
        mycontainer = self._get_value(key, **kw)
        if mycontainer.has_current_value():
            mycontainer.clear_value()
    remove = remove_value

    def _get_value(self, key, **kw):
        if isinstance(key, unicode):
            key = key.encode('ascii', 'backslashreplace')

        if 'type' in kw:
            return self._legacy_get_value(key, **kw)

        kw.setdefault('expiretime', self.expiretime)
        kw.setdefault('starttime', self.starttime)
        
        return container.Value(key, self.namespace, **kw)
    
    @util.deprecated("Specifying a "
            "'type' and other namespace configuration with cache.get()/put()/etc. "
            "is deprecated. Specify 'type' and other namespace configuration to "
            "cache_manager.get_cache() and/or the Cache constructor instead.")
    def _legacy_get_value(self, key, type, **kw):
        expiretime = kw.pop('expiretime', self.expiretime)
        starttime = kw.pop('starttime', None)
        createfunc = kw.pop('createfunc', None)
        kwargs = self.nsargs.copy()
        kwargs.update(kw)
        c = Cache(self.namespace.namespace, type=type, **kwargs)
        return c._get_value(key, expiretime=expiretime, createfunc=createfunc, 
                            starttime=starttime)
    
    def clear(self):
        """Clear all the values from the namespace"""
        self.namespace.remove()
    
    # dict interface
    def __getitem__(self, key):
        return self.get(key)
    
    def __contains__(self, key):
        return self._get_value(key).has_current_value()
    
    def has_key(self, key):
        return key in self
    
    def __delitem__(self, key):
        self.remove_value(key)
    
    def __setitem__(self, key, value):
        self.put(key, value)


class CacheManager(object):
    def __init__(self, **kwargs):
        """Initialize a CacheManager object with a set of options
        
        Options should be parsed with the
        :func:`~beaker.util.parse_cache_config_options` function to
        ensure only valid options are used.
        
        """
        self.kwargs = kwargs
        self.regions = kwargs.pop('cache_regions', {})
        
        # Add these regions to the module global
        cache_regions.update(self.regions)
    
    def get_cache(self, name, **kwargs):
        kw = self.kwargs.copy()
        kw.update(kwargs)
        return Cache._get_cache(name, kw)
    
    def get_cache_region(self, name, region):
        if region not in self.regions:
            raise BeakerException('Cache region not configured: %s' % region)
        kw = self.regions[region]
        return Cache._get_cache(name, kw)
    
    def region(self, region, *args):
        """Decorate a function to cache itself using a cache region
        
        The region decorator requires arguments if there are more than
        2 of the same named function, in the same module. This is
        because the namespace used for the functions cache is based on
        the functions name and the module.
        
        
        Example::
            
            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)
            
            
            def populate_things():
                
                @cache.region('short_term', 'some_data')
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)
                
                return load('rabbits', 20, 0)
        
        .. note::
            
            The function being decorated must only be called with
            positional arguments.
        
        """
        return cache_region(region, *args)

    def region_invalidate(self, namespace, region, *args):
        """Invalidate a cache region namespace or decorated function
        
        This function only invalidates cache spaces created with the
        cache_region decorator.
        
        :param namespace: Either the namespace of the result to invalidate, or the
           name of the cached function
        
        :param region: The region the function was cached to. If the function was
            cached to a single region then this argument can be None
        
        :param args: Arguments that were used to differentiate the cached
            function as well as the arguments passed to the decorated
            function

        Example::
            
            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)
            
            def populate_things(invalidate=False):
                
                @cache.region('short_term', 'some_data')
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)
                
                # If the results should be invalidated first
                if invalidate:
                    cache.region_invalidate(load, None, 'some_data',
                                            'rabbits', 20, 0)
                return load('rabbits', 20, 0)
            
        
        """
        return region_invalidate(namespace, region, *args)
        if callable(namespace):
            if not region:
                region = namespace._arg_region
            namespace = namespace._arg_namespace

        if not region:
            raise BeakerException("Region or callable function "
                                    "namespace is required")
        else:
            region = self.regions[region]
        
        cache = self.get_cache(namespace, **region)
        cache_key = " ".join(str(x) for x in args)
        cache.remove_value(cache_key)

    def cache(self, *args, **kwargs):
        """Decorate a function to cache itself with supplied parameters

        :param args: Used to make the key unique for this function, as in region()
            above.

        :param kwargs: Parameters to be passed to get_cache(), will override defaults

        Example::

            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)
            
            
            def populate_things():
                
                @cache.cache('mycache', expire=15)
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)
                
                return load('rabbits', 20, 0)
        
        .. note::
            
            The function being decorated must only be called with
            positional arguments. 

        """
        cache = [None]
        key = " ".join(str(x) for x in args)
        
        def decorate(func):
            namespace = util.func_namespace(func)
            def cached(*args):
                if not cache[0]:
                    cache[0] = self.get_cache(namespace, **kwargs)
                cache_key = key + " " + " ".join(str(x) for x in args)
                def go():
                    return func(*args)
                return cache[0].get_value(cache_key, createfunc=go)
            cached._arg_namespace = namespace
            return cached
        return decorate

    def invalidate(self, func, *args, **kwargs):
        """Invalidate a cache decorated function
        
        This function only invalidates cache spaces created with the
        cache decorator.
        
        :param func: Decorated function to invalidate
        
        :param args: Used to make the key unique for this function, as in region()
            above.

        :param kwargs: Parameters that were passed for use by get_cache(), note that
            this is only required if a ``type`` was specified for the
            function

        Example::
            
            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)
            
            
            def populate_things(invalidate=False):
                
                @cache.cache('mycache', type="file", expire=15)
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)
                
                # If the results should be invalidated first
                if invalidate:
                    cache.invalidate(load, 'mycache', 'rabbits', 20, 0, type="file")
                return load('rabbits', 20, 0)
        
        """
        namespace = func._arg_namespace

        cache = self.get_cache(namespace, **kwargs)
        cache_key = " ".join(str(x) for x in args)
        cache.remove_value(cache_key)
