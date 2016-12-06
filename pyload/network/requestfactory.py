# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object
from .Bucket import Bucket

from pyload.plugins.network.DefaultRequest import DefaultRequest, DefaultDownload


class RequestFactory(object):
    def __init__(self, core):
        self.core = core
        self.bucket = Bucket()
        self.updateBucket()

        self.core.evm.listenTo("config:changed", self.updateConfig)

    def getURL(self, *args, **kwargs):
        """ see HTTPRequest for argument list """
        h = DefaultRequest(self.getConfig())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep

        ########## old api methods above

    def getRequest(self, context=None, klass=DefaultRequest):
        """ Creates a request with new or given context """
        # also accepts the context class directly
        if isinstance(context, klass.CONTEXT_CLASS):
            return klass(self.getConfig(), context)
        elif context:
            return klass(*context)
        else:
            return klass(self.getConfig())

    def getDownloadRequest(self, request=None, klass=DefaultDownload):
        """ Instantiates a instance for downloading """
        # TODO: load with plugin manager
        return klass(self.bucket, request)

    def getInterface(self):
        return self.core.config["download"]["interface"]

    def getProxies(self):
        """ returns a proxy list for the request classes """
        if not self.core.config["proxy"]["proxy"]:
            return {}
        else:
            type = "http"
            setting = self.core.config["proxy"]["type"].lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if self.core.config["proxy"]["username"] and self.core.config["proxy"]["username"].lower() != "none":
                username = self.core.config["proxy"]["username"]

            pw = None
            if self.core.config["proxy"]["password"] and self.core.config["proxy"]["password"].lower() != "none":
                pw = self.core.config["proxy"]["password"]

            return {
                "type": type,
                "address": self.core.config["proxy"]["address"],
                "port": self.core.config["proxy"]["port"],
                "username": username,
                "password": pw,
            }

    def updateConfig(self, section, option, value):
        """ Updates the bucket when a config value changed """
        if option in ("limit_speed", "max_speed"):
            self.updateBucket()

    def getConfig(self):
        """returns options needed for pycurl"""
        return {"interface": self.getInterface(),
                "proxies": self.getProxies(),
                "ipv6": self.core.config["download"]["ipv6"]}

    def updateBucket(self):
        """ set values in the bucket according to settings"""
        if not self.core.config["download"]["limit_speed"]:
            self.bucket.setRate(-1)
        else:
            self.bucket.setRate(self.core.config["download"]["max_speed"] * 1024)

# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return pyreq.getRequest(*args, **kwargs)
