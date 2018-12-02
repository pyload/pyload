# -*- coding: utf-8 -*-
# AUTHOR: mkaay, RaNaN

from builtins import REQUESTS, object
from threading import Lock

from pyload.plugins.utils import lock

from .browser import Browser
from .bucket import Bucket
from .cookie_jar import CookieJar
from .http.http_request import HTTPRequest
from .xdcc.xdcc_request import XDCCRequest


class RequestFactory(object):
    def __init__(self, core):
        self.lock = Lock()
        self.pyload = core
        self._ = core._
        self.bucket = Bucket()
        self.updateBucket()
        self.cookiejars = {}

    def iface(self):
        return self.pyload.config.get("download", "interface")

    @lock
    def getRequest(self, pluginName, account=None, type="HTTP", **kwargs):
        options = self.getOptions()
        options.update(kwargs)  #: submit kwargs as additional options

        if type == "XDCC":
            req = XDCCRequest(self.bucket, options)

        else:
            req = Browser(self.bucket, options)

            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(CookieJar(pluginName))

        return req

    def getHTTPRequest(self, **kwargs):
        """
        returns a http request, dont forget to close it !
        """
        options = self.getOptions()
        options.update(kwargs)  #: submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)

    def getURL(self, *args, **kwargs):
        """
        see HTTPRequest for argument list.
        """
        with HTTPRequest(None, self.getOptions()) as h:
            rep = h.load(*args, **kwargs)
        return rep

    def getCookieJar(self, pluginName, account=None):
        if (pluginName, account) in self.cookiejars:
            return self.cookiejars[(pluginName, account)]

        cj = CookieJar(pluginName, account)
        self.cookiejars[(pluginName, account)] = cj
        return cj

    def getProxies(self):
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

    def getOptions(self):
        """
        returns options needed for pycurl.
        """
        return {
            "interface": self.iface(),
            "proxies": self.getProxies(),
            "ipv6": self.pyload.config.get("download", "ipv6"),
        }

    def updateBucket(self):
        """
        set values in the bucket according to settings.
        """
        if not self.pyload.config.get("download", "limit_speed"):
            self.bucket.set_rate(-1)
        else:
            self.bucket.set_rate(self.pyload.config.get("download", "max_speed") << 10)


# needs REQUESTS in global namespace
def getURL(*args, **kwargs):
    return REQUESTS.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return REQUESTS.getHTTPRequest()
