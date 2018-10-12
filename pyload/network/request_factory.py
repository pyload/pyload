# -*- coding: utf-8 -*-
# @author: mkaay, RaNaN

from builtins import object, pyreq
from threading import Lock

from pyload.network.browser import Browser
from pyload.network.bucket import Bucket
from pyload.network.cookie_factory import CookieJar
from pyload.network.http_request import HTTPRequest
from pyload.network.xdcc_request import XDCCRequest


class RequestFactory(object):
    def __init__(self, core):
        self.lock = Lock()
        self.pyload = core
        self.bucket = Bucket()
        self.updateBucket()
        self.cookiejars = {}

    def iface(self):
        return self.pyload.config["download"]["interface"]

    def getRequest(self, pluginName, account=None, type="HTTP", **kwargs):
        self.lock.acquire()

        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options

        if type == "XDCC":
            req = XDCCRequest(self.bucket, options)

        else:
            req = Browser(self.bucket, options)

            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(CookieJar(pluginName))

        self.lock.release()
        return req

    def getHTTPRequest(self, **kwargs):
        """
        returns a http request, dont forget to close it !
        """
        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)

    def getURL(self, *args, **kwargs):
        """
        see HTTPRequest for argument list.
        """
        h = HTTPRequest(None, self.getOptions())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

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
        if not self.pyload.config["proxy"]["proxy"]:
            return {}
        else:
            type = "http"
            setting = self.pyload.config["proxy"]["type"].lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if (
                self.pyload.config["proxy"]["username"]
                and self.pyload.config["proxy"]["username"].lower() != "none"
            ):
                username = self.pyload.config["proxy"]["username"]

            pw = None
            if (
                self.pyload.config["proxy"]["password"]
                and self.pyload.config["proxy"]["password"].lower() != "none"
            ):
                pw = self.pyload.config["proxy"]["password"]

            return {
                "type": type,
                "address": self.pyload.config["proxy"]["address"],
                "port": self.pyload.config["proxy"]["port"],
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
            "ipv6": self.pyload.config["download"]["ipv6"],
        }

    def updateBucket(self):
        """
        set values in the bucket according to settings.
        """
        if not self.pyload.config["download"]["limit_speed"]:
            self.bucket.setRate(-1)
        else:
            self.bucket.setRate(self.pyload.config["download"]["max_speed"] * 1024)


# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return pyreq.getHTTPRequest()
