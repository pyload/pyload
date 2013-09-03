# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2013 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from Bucket import Bucket

from pyload.plugins.network.DefaultRequest import DefaultRequest, DefaultDownload


class RequestFactory:
    def __init__(self, core):
        self.core = core
        self.bucket = Bucket()
        self.updateBucket()

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
        return self.config["download"]["interface"]

    def getProxies(self):
        """ returns a proxy list for the request classes """
        if not self.config["proxy"]["proxy"]:
            return {}
        else:
            type = "http"
            setting = self.config["proxy"]["type"].lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if self.config["proxy"]["username"] and self.config["proxy"]["username"].lower() != "none":
                username = self.config["proxy"]["username"]

            pw = None
            if self.config["proxy"]["password"] and self.config["proxy"]["password"].lower() != "none":
                pw = self.config["proxy"]["password"]

            return {
                "type": type,
                "address": self.config["proxy"]["address"],
                "port": self.config["proxy"]["port"],
                "username": username,
                "password": pw,
            }

    def getConfig(self):
        """returns options needed for pycurl"""
        return {"interface": self.getInterface(),
                "proxies": self.getProxies(),
                "ipv6": self.config["download"]["ipv6"]}

    def updateBucket(self):
        """ set values in the bucket according to settings"""
        if not self.config["download"]["limit_speed"]:
            self.bucket.setRate(-1)
        else:
            self.bucket.setRate(self.config["download"]["max_speed"] * 1024)

# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return pyreq.getRequest(*args, **kwargs)
