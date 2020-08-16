# -*- coding: utf-8 -*-

from threading import Lock

from ..utils.old import lock
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
                req.set_cookie_jar(cj)
            else:
                req.set_cookie_jar(CookieJar(plugin_name))

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
        self.cookiejars[(plugin_name, account)] = cj
        return cj

    def get_proxies(self):
        """
        returns a proxy list for the request classes.
        """
        if not self.pyload.config.get("proxy", "enabled"):
            return {}
        else:
            type = "http"
            setting = self.pyload.config.get("proxy", "type").lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if (
                self.pyload.config.get("proxy", "username")
                and self.pyload.config.get("proxy", "username").lower() != "none"
            ):
                username = self.pyload.config.get("proxy", "username")

            pw = None
            if (
                self.pyload.config.get("proxy", "password")
                and self.pyload.config.get("proxy", "password").lower() != "none"
            ):
                pw = self.pyload.config.get("proxy", "password")

            return {
                "type": type,
                "host": self.pyload.config.get("proxy", "host"),
                "port": self.pyload.config.get("proxy", "port"),
                "username": username,
                "password": pw,
            }

    def get_options(self):
        """
        returns options needed for pycurl.
        """
        return {
            "interface": self.iface(),
            "proxies": self.get_proxies(),
            "ipv6": self.pyload.config.get("download", "ipv6"),
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
