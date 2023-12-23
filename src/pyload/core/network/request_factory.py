# -*- coding: utf-8 -*-

from threading import Lock

from ..utils.struct.lock import lock
from .browser import Browser
from .bucket import Bucket
from .cookie_jar import CookieJar
from .http.http_request import HTTPRequest
from .xdcc.request import XDCCRequest

DEFAULT_REQUEST = None


class RequestFactory:
    def __init__(self, core):
        self.lock = Lock()
        self.pyload = core
        self._ = core._
        self.bucket = Bucket()
        self.update_bucket()
        self.cookiejars = {}

        # TODO: Rewrite...
        global DEFAULT_REQUEST
        if not DEFAULT_REQUEST:
            DEFAULT_REQUEST = self

    def iface(self):
        return self.pyload.config.get("download", "interface")

    @lock
    def get_request(self, plugin_name, account=None, type="HTTP", **kwargs):
        options = self.get_options()
        options.update(kwargs)  #: submit kwargs as additional options

        if type == "XDCC":
            req = XDCCRequest(self.bucket, options)

        else:
            req = Browser(self.bucket, options)

            if account:
                cj = self.get_cookie_jar(plugin_name, account)
            else:
                cj = CookieJar(plugin_name)

            req.set_cookie_jar(cj)

        return req

    def get_http_request(self, **kwargs):
        """
        returns a http request, dont forget to close it !
        """
        options = self.get_options()
        options.update(kwargs)  #: submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)

    def get_url(self, *args, **kwargs):
        """
        see HTTPRequest for argument list.
        """
        with HTTPRequest(None, self.get_options()) as h:
            rep = h.load(*args, **kwargs)
        return rep

    def get_cookie_jar(self, plugin_name, account=None):
        if (plugin_name, account) in self.cookiejars:
            return self.cookiejars[(plugin_name, account)]

        cj = CookieJar(plugin_name, account)
        if account:
            self.cookiejars[(plugin_name, account)] = cj
        return cj

    def remove_cookie_jar(self, plugin_name, account):
        self.cookiejars.pop((plugin_name, account), None)

    def get_proxies(self):
        """
        returns proxy related options.
        """
        if not self.pyload.config.get("proxy", "enabled"):
            return {}
        else:
            proxy_type = self.pyload.config.get("proxy", "type")
            socks_resolve_dns = self.pyload.config.get("proxy", "socks_resolve_dns")
            proxy_host = self.pyload.config.get("proxy", "host")
            proxy_port = self.pyload.config.get("proxy", "port")
            proxy_username = self.pyload.config.get("proxy", "username") or None
            proxy_password = self.pyload.config.get("proxy", "password") or None

            return {
                "type": proxy_type,
                "socks_resolve_dns": socks_resolve_dns,
                "host": proxy_host,
                "port": proxy_port,
                "username": proxy_username,
                "password": proxy_password,
            }

    def get_options(self):
        """
        returns options needed for pycurl.
        """
        return {
            "interface": self.iface(),
            "proxies": self.get_proxies(),
            "ipv6": self.pyload.config.get("download", "ipv6"),
            "ssl_verify": self.pyload.config.get("general", "ssl_verify"),
        }

    def update_bucket(self):
        """
        set values in the bucket according to settings.
        """
        if not self.pyload.config.get("download", "limit_speed"):
            self.bucket.set_rate(-1)
        else:
            self.bucket.set_rate(self.pyload.config.get("download", "max_speed") << 10)


def get_url(*args, **kwargs):
    return DEFAULT_REQUEST.get_url(*args, **kwargs)


def get_request(*args, **kwargs):
    return DEFAULT_REQUEST.get_http_request()
