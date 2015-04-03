import Cookie
import os
import random
import time
from datetime import datetime, timedelta
    
from beaker.crypto import hmac as HMAC, hmac_sha1 as SHA1, md5
from beaker.util import pickle

from beaker import crypto
from beaker.cache import clsmap
from beaker.exceptions import BeakerException, InvalidCryptoBackendError
from base64 import b64encode, b64decode


__all__ = ['SignedCookie', 'Session']

getpid = hasattr(os, 'getpid') and os.getpid or (lambda : '')

class SignedCookie(Cookie.BaseCookie):
    """Extends python cookie to give digital signature support"""
    def __init__(self, secret, input=None):
        self.secret = secret
        Cookie.BaseCookie.__init__(self, input)
    
    def value_decode(self, val):
        val = val.strip('"')
        sig = HMAC.new(self.secret, val[40:], SHA1).hexdigest()
        
        # Avoid timing attacks
        invalid_bits = 0
        input_sig = val[:40]
        if len(sig) != len(input_sig):
            return None, val
        
        for a, b in zip(sig, input_sig):
            invalid_bits += a != b
        
        if invalid_bits:
            return None, val
        else:
            return val[40:], val
    
    def value_encode(self, val):
        sig = HMAC.new(self.secret, val, SHA1).hexdigest()
        return str(val), ("%s%s" % (sig, val))


class Session(dict):
    """Session object that uses container package for storage.
    
    ``key``
        The name the cookie should be set to.
    ``timeout``
        How long session data is considered valid. This is used 
        regardless of the cookie being present or not to determine
        whether session data is still valid.
    ``cookie_domain``
        Domain to use for the cookie.
    ``secure``
        Whether or not the cookie should only be sent over SSL.
    """
    def __init__(self, request, id=None, invalidate_corrupt=False,
                 use_cookies=True, type=None, data_dir=None,
                 key='beaker.session.id', timeout=None, cookie_expires=True,
                 cookie_domain=None, secret=None, secure=False,
                 namespace_class=None, **namespace_args):
        if not type:
            if data_dir:
                self.type = 'file'
            else:
                self.type = 'memory'
        else:
            self.type = type

        self.namespace_class = namespace_class or clsmap[self.type]

        self.namespace_args = namespace_args
        
        self.request = request
        self.data_dir = data_dir
        self.key = key
        
        self.timeout = timeout
        self.use_cookies = use_cookies
        self.cookie_expires = cookie_expires
        
        # Default cookie domain/path
        self._domain = cookie_domain
        self._path = '/'
        self.was_invalidated = False
        self.secret = secret
        self.secure = secure
        self.id = id
        self.accessed_dict = {}
        
        if self.use_cookies:
            cookieheader = request.get('cookie', '')
            if secret:
                try:
                    self.cookie = SignedCookie(secret, input=cookieheader)
                except Cookie.CookieError:
                    self.cookie = SignedCookie(secret, input=None)
            else:
                self.cookie = Cookie.SimpleCookie(input=cookieheader)
            
            if not self.id and self.key in self.cookie:
                self.id = self.cookie[self.key].value
        
        self.is_new = self.id is None
        if self.is_new:
            self._create_id()
            self['_accessed_time'] = self['_creation_time'] = time.time()
        else:
            try:
                self.load()
            except:
                if invalidate_corrupt:
                    self.invalidate()
                else:
                    raise
        
    def _create_id(self):
        self.id = md5(
            md5("%f%s%f%s" % (time.time(), id({}), random.random(),
                              getpid())).hexdigest(), 
        ).hexdigest()
        self.is_new = True
        self.last_accessed = None
        if self.use_cookies:
            self.cookie[self.key] = self.id
            if self._domain:
                self.cookie[self.key]['domain'] = self._domain
            if self.secure:
                self.cookie[self.key]['secure'] = True
            self.cookie[self.key]['path'] = self._path
            if self.cookie_expires is not True:
                if self.cookie_expires is False:
                    expires = datetime.fromtimestamp( 0x7FFFFFFF )
                elif isinstance(self.cookie_expires, timedelta):
                    expires = datetime.today() + self.cookie_expires
                elif isinstance(self.cookie_expires, datetime):
                    expires = self.cookie_expires
                else:
                    raise ValueError("Invalid argument for cookie_expires: %s"
                                     % repr(self.cookie_expires))
                self.cookie[self.key]['expires'] = \
                    expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT" )
            self.request['cookie_out'] = self.cookie[self.key].output(header='')
            self.request['set_cookie'] = False
    
    def created(self):
        return self['_creation_time']
    created = property(created)
    
    def _set_domain(self, domain):
        self['_domain'] = domain
        self.cookie[self.key]['domain'] = domain
        self.request['cookie_out'] = self.cookie[self.key].output(header='')
        self.request['set_cookie'] = True
    
    def _get_domain(self):
        return self._domain
    
    domain = property(_get_domain, _set_domain)
    
    def _set_path(self, path):
        self['_path'] = path
        self.cookie[self.key]['path'] = path
        self.request['cookie_out'] = self.cookie[self.key].output(header='')
        self.request['set_cookie'] = True
    
    def _get_path(self):
        return self._path
    
    path = property(_get_path, _set_path)

    def _delete_cookie(self):
        self.request['set_cookie'] = True
        self.cookie[self.key] = self.id
        if self._domain:
            self.cookie[self.key]['domain'] = self._domain
        if self.secure:
            self.cookie[self.key]['secure'] = True
        self.cookie[self.key]['path'] = '/'
        expires = datetime.today().replace(year=2003)
        self.cookie[self.key]['expires'] = \
            expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT" )
        self.request['cookie_out'] = self.cookie[self.key].output(header='')
        self.request['set_cookie'] = True

    def delete(self):
        """Deletes the session from the persistent storage, and sends
        an expired cookie out"""
        if self.use_cookies:
            self._delete_cookie()
        self.clear()

    def invalidate(self):
        """Invalidates this session, creates a new session id, returns
        to the is_new state"""
        self.clear()
        self.was_invalidated = True
        self._create_id()
        self.load()
    
    def load(self):
        "Loads the data from this session from persistent storage"
        self.namespace = self.namespace_class(self.id,
            data_dir=self.data_dir, digest_filenames=False,
            **self.namespace_args)
        now = time.time()
        self.request['set_cookie'] = True
        
        self.namespace.acquire_read_lock()
        timed_out = False
        try:
            self.clear()
            try:
                session_data = self.namespace['session']

                # Memcached always returns a key, its None when its not
                # present
                if session_data is None:
                    session_data = {
                        '_creation_time':now,
                        '_accessed_time':now
                    }
                    self.is_new = True
            except (KeyError, TypeError):
                session_data = {
                    '_creation_time':now,
                    '_accessed_time':now
                }
                self.is_new = True
            
            if self.timeout is not None and \
               now - session_data['_accessed_time'] > self.timeout:
                timed_out= True
            else:
                # Properly set the last_accessed time, which is different
                # than the *currently* _accessed_time
                if self.is_new or '_accessed_time' not in session_data:
                    self.last_accessed = None
                else:
                    self.last_accessed = session_data['_accessed_time']
                
                # Update the current _accessed_time
                session_data['_accessed_time'] = now
                self.update(session_data)
                self.accessed_dict = session_data.copy()                
        finally:
            self.namespace.release_read_lock()
        if timed_out:
            self.invalidate()
    
    def save(self, accessed_only=False):
        """Saves the data for this session to persistent storage
        
        If accessed_only is True, then only the original data loaded
        at the beginning of the request will be saved, with the updated
        last accessed time.
        
        """
        # Look to see if its a new session that was only accessed
        # Don't save it under that case
        if accessed_only and self.is_new:
            return None
        
        if not hasattr(self, 'namespace'):
            self.namespace = self.namespace_class(
                                    self.id, 
                                    data_dir=self.data_dir,
                                    digest_filenames=False, 
                                    **self.namespace_args)
        
        self.namespace.acquire_write_lock()
        try:
            if accessed_only:
                data = dict(self.accessed_dict.items())
            else:
                data = dict(self.items())
            
            # Save the data
            if not data and 'session' in self.namespace:
                del self.namespace['session']
            else:
                self.namespace['session'] = data
        finally:
            self.namespace.release_write_lock()
        if self.is_new:
            self.request['set_cookie'] = True
    
    def revert(self):
        """Revert the session to its original state from its first
        access in the request"""
        self.clear()
        self.update(self.accessed_dict)
    
    # TODO: I think both these methods should be removed.  They're from
    # the original mod_python code i was ripping off but they really
    # have no use here.
    def lock(self):
        """Locks this session against other processes/threads.  This is
        automatic when load/save is called.
        
        ***use with caution*** and always with a corresponding 'unlock'
        inside a "finally:" block, as a stray lock typically cannot be
        unlocked without shutting down the whole application.

        """
        self.namespace.acquire_write_lock()

    def unlock(self):
        """Unlocks this session against other processes/threads.  This
        is automatic when load/save is called.

        ***use with caution*** and always within a "finally:" block, as
        a stray lock typically cannot be unlocked without shutting down
        the whole application.

        """
        self.namespace.release_write_lock()

class CookieSession(Session):
    """Pure cookie-based session
    
    Options recognized when using cookie-based sessions are slightly
    more restricted than general sessions.
    
    ``key``
        The name the cookie should be set to.
    ``timeout``
        How long session data is considered valid. This is used 
        regardless of the cookie being present or not to determine
        whether session data is still valid.
    ``encrypt_key``
        The key to use for the session encryption, if not provided the
        session will not be encrypted.
    ``validate_key``
        The key used to sign the encrypted session
    ``cookie_domain``
        Domain to use for the cookie.
    ``secure``
        Whether or not the cookie should only be sent over SSL.
    
    """
    def __init__(self, request, key='beaker.session.id', timeout=None,
                 cookie_expires=True, cookie_domain=None, encrypt_key=None,
                 validate_key=None, secure=False, **kwargs):
        
        if not crypto.has_aes and encrypt_key:
            raise InvalidCryptoBackendError("No AES library is installed, can't generate "
                                  "encrypted cookie-only Session.")
        
        self.request = request
        self.key = key
        self.timeout = timeout
        self.cookie_expires = cookie_expires
        self.encrypt_key = encrypt_key
        self.validate_key = validate_key
        self.request['set_cookie'] = False
        self.secure = secure
        self._domain = cookie_domain
        self._path = '/'
        
        try:
            cookieheader = request['cookie']
        except KeyError:
            cookieheader = ''
        
        if validate_key is None:
            raise BeakerException("No validate_key specified for Cookie only "
                                  "Session.")
        
        try:
            self.cookie = SignedCookie(validate_key, input=cookieheader)
        except Cookie.CookieError:
            self.cookie = SignedCookie(validate_key, input=None)
        
        self['_id'] = self._make_id()
        self.is_new = True
        
        # If we have a cookie, load it
        if self.key in self.cookie and self.cookie[self.key].value is not None:
            self.is_new = False
            try:
                self.update(self._decrypt_data())
            except:
                pass
            if self.timeout is not None and time.time() - \
               self['_accessed_time'] > self.timeout:
                self.clear()
            self.accessed_dict = self.copy()
            self._create_cookie()
    
    def created(self):
        return self['_creation_time']
    created = property(created)
    
    def id(self):
        return self['_id']
    id = property(id)

    def _set_domain(self, domain):
        self['_domain'] = domain
        self._domain = domain
        
    def _get_domain(self):
        return self._domain
    
    domain = property(_get_domain, _set_domain)
    
    def _set_path(self, path):
        self['_path'] = path
        self._path = path
    
    def _get_path(self):
        return self._path
    
    path = property(_get_path, _set_path)

    def _encrypt_data(self):
        """Serialize, encipher, and base64 the session dict"""
        if self.encrypt_key:
            nonce = b64encode(os.urandom(40))[:8]
            encrypt_key = crypto.generateCryptoKeys(self.encrypt_key,
                                             self.validate_key + nonce, 1)
            data = pickle.dumps(self.copy(), 2)
            return nonce + b64encode(crypto.aesEncrypt(data, encrypt_key))
        else:
            data = pickle.dumps(self.copy(), 2)
            return b64encode(data)
    
    def _decrypt_data(self):
        """Bas64, decipher, then un-serialize the data for the session
        dict"""
        if self.encrypt_key:
            nonce = self.cookie[self.key].value[:8]
            encrypt_key = crypto.generateCryptoKeys(self.encrypt_key,
                                             self.validate_key + nonce, 1)
            payload = b64decode(self.cookie[self.key].value[8:])
            data = crypto.aesDecrypt(payload, encrypt_key)
            return pickle.loads(data)
        else:
            data = b64decode(self.cookie[self.key].value)
            return pickle.loads(data)
    
    def _make_id(self):
        return md5(md5(
            "%f%s%f%s" % (time.time(), id({}), random.random(), getpid())
            ).hexdigest()
        ).hexdigest()
    
    def save(self, accessed_only=False):
        """Saves the data for this session to persistent storage"""
        if accessed_only and self.is_new:
            return
        if accessed_only:
            self.clear()
            self.update(self.accessed_dict)
        self._create_cookie()
    
    def expire(self):
        """Delete the 'expires' attribute on this Session, if any."""
        
        self.pop('_expires', None)
        
    def _create_cookie(self):
        if '_creation_time' not in self:
            self['_creation_time'] = time.time()
        if '_id' not in self:
            self['_id'] = self._make_id()
        self['_accessed_time'] = time.time()
        
        if self.cookie_expires is not True:
            if self.cookie_expires is False:
                expires = datetime.fromtimestamp( 0x7FFFFFFF )
            elif isinstance(self.cookie_expires, timedelta):
                expires = datetime.today() + self.cookie_expires
            elif isinstance(self.cookie_expires, datetime):
                expires = self.cookie_expires
            else:
                raise ValueError("Invalid argument for cookie_expires: %s"
                                 % repr(self.cookie_expires))
            self['_expires'] = expires
        elif '_expires' in self:
            expires = self['_expires']
        else:
            expires = None

        val = self._encrypt_data()
        if len(val) > 4064:
            raise BeakerException("Cookie value is too long to store")
        
        self.cookie[self.key] = val
        if '_domain' in self:
            self.cookie[self.key]['domain'] = self['_domain']
        elif self._domain:
            self.cookie[self.key]['domain'] = self._domain
        if self.secure:
            self.cookie[self.key]['secure'] = True
        
        self.cookie[self.key]['path'] = self.get('_path', '/')
        
        if expires:
            self.cookie[self.key]['expires'] = \
                expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT" )
        self.request['cookie_out'] = self.cookie[self.key].output(header='')
        self.request['set_cookie'] = True
    
    def delete(self):
        """Delete the cookie, and clear the session"""
        # Send a delete cookie request
        self._delete_cookie()
        self.clear()
    
    def invalidate(self):
        """Clear the contents and start a new session"""
        self.delete()
        self['_id'] = self._make_id()


class SessionObject(object):
    """Session proxy/lazy creator
    
    This object proxies access to the actual session object, so that in
    the case that the session hasn't been used before, it will be
    setup. This avoid creating and loading the session from persistent
    storage unless its actually used during the request.
    
    """
    def __init__(self, environ, **params):
        self.__dict__['_params'] = params
        self.__dict__['_environ'] = environ
        self.__dict__['_sess'] = None
        self.__dict__['_headers'] = []
    
    def _session(self):
        """Lazy initial creation of session object"""
        if self.__dict__['_sess'] is None:
            params = self.__dict__['_params']
            environ = self.__dict__['_environ']
            self.__dict__['_headers'] = req = {'cookie_out':None}
            req['cookie'] = environ.get('HTTP_COOKIE')
            if params.get('type') == 'cookie':
                self.__dict__['_sess'] = CookieSession(req, **params)
            else:
                self.__dict__['_sess'] = Session(req, use_cookies=True,
                                                 **params)
        return self.__dict__['_sess']
    
    def __getattr__(self, attr):
        return getattr(self._session(), attr)
    
    def __setattr__(self, attr, value):
        setattr(self._session(), attr, value)
    
    def __delattr__(self, name):
        self._session().__delattr__(name)
    
    def __getitem__(self, key):
        return self._session()[key]
    
    def __setitem__(self, key, value):
        self._session()[key] = value
    
    def __delitem__(self, key):
        self._session().__delitem__(key)
    
    def __repr__(self):
        return self._session().__repr__()
    
    def __iter__(self):
        """Only works for proxying to a dict"""
        return iter(self._session().keys())
    
    def __contains__(self, key):
        return self._session().has_key(key)
    
    def get_by_id(self, id):
        """Loads a session given a session ID"""
        params = self.__dict__['_params']
        session = Session({}, use_cookies=False, id=id, **params)
        if session.is_new:
            return None
        return session
    
    def save(self):
        self.__dict__['_dirty'] = True
    
    def delete(self):
        self.__dict__['_dirty'] = True
        self._session().delete()
    
    def persist(self):
        """Persist the session to the storage
        
        If its set to autosave, then the entire session will be saved
        regardless of if save() has been called. Otherwise, just the
        accessed time will be updated if save() was not called, or
        the session will be saved if save() was called.
        
        """
        if self.__dict__['_params'].get('auto'):
            self._session().save()
        else:
            if self.__dict__.get('_dirty'):
                self._session().save()
            else:
                self._session().save(accessed_only=True)
    
    def dirty(self):
        return self.__dict__.get('_dirty', False)
    
    def accessed(self):
        """Returns whether or not the session has been accessed"""
        return self.__dict__['_sess'] is not None
