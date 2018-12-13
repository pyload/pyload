# -*- coding: utf-8 -*-
# AUTHOR: mkaay, RaNaN

import time
from builtins import object
from datetime import timedelta

class CookieJar(object):
    def __init__(self, pluginname, account=None):
        self.cookies = {}
        self.plugin = pluginname
        self.account = account

    def addCookies(self, clist):
        for c in clist:
            name = c.split("\t")[5]
            self.cookies[name] = c

    def getCookies(self):
        return list(self.cookies.values())

    def parseCookie(self, name):
        if name in self.cookies:
            return self.cookies[name].split("\t")[6]
        else:
            return None

    def getCookie(self, name):
        return self.parseCookie(name)

    def setCookie(
        self, domain, name, value, path="/", exp=time.time() + timedelta(hours=744).seconds  #: 31 days retention
    ):
        self.cookies[
            name
        ] = f".{domain}    TRUE    {path}    FALSE    {exp}    {name}    {value}"

    def clear(self):
        self.cookies = {}
