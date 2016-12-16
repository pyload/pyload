# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object
from .bucket import Bucket

from pyload.plugins.network.defaultrequest import DefaultRequest, DefaultDownload


class RequestFactory(object):
    def __init__(self, core):
        self.pyload = core
        self.bucket = Bucket()
        self.updateBucket()

        self.pyload.evm.listen_to("config:changed", self.updateConfig)

    def get_url(self, *args, **kwargs):
        """ see HTTPRequest for argument list """
        h = DefaultRequest(self.getConfig())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep

        ########## old api methods above

    def get_request(self, context=None, klass=DefaultRequest):
        """ Creates a request with new or given context """
        # also accepts the context class directly
        if isinstance(context, klass.CONTEXT_CLASS):
            return klass(self.getConfig(), context)
        elif context:
            return klass(*context)
        else:
            return klass(self.getConfig())

    def get_download_request(self, request=None, klass=DefaultDownload):
        """ Instantiates a instance for downloading """
        # TODO: load with plugin manager
        return klass(self.bucket, request)

    def get_interface(self):
        return self.pyload.config["download"]["interface"]

    def get_proxies(self):
        """ returns a proxy list for the request classes """
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
            if self.pyload.config["proxy"]["username"] and self.pyload.config["proxy"]["username"].lower() != "none":
                username = self.pyload.config["proxy"]["username"]

            pw = None
            if self.pyload.config["proxy"]["password"] and self.pyload.config["proxy"]["password"].lower() != "none":
                pw = self.pyload.config["proxy"]["password"]

            return {
                "type": type,
                "address": self.pyload.config["proxy"]["address"],
                "port": self.pyload.config["proxy"]["port"],
                "username": username,
                "password": pw,
            }

    def update_config(self, section, option, value):
        """ Updates the bucket when a config value changed """
        if option in ("limit_speed", "max_speed"):
            self.updateBucket()

    def get_config(self):
        """returns options needed for pycurl"""
        return {"interface": self.getInterface(),
                "proxies": self.getProxies(),
                "ipv6": self.pyload.config["download"]["ipv6"]}

    def update_bucket(self):
        """ set values in the bucket according to settings"""
        if not self.pyload.config["download"]["limit_speed"]:
            self.bucket.set_rate(-1)
        else:
            self.bucket.setRate(self.pyload.config["download"]["max_speed"] * 1024)

# needs pyreq in global namespace
def get_url(*args, **kwargs):
    return pyreq.get_url(*args, **kwargs)


def get_request(*args, **kwargs):
    return pyreq.getRequest(*args, **kwargs)
