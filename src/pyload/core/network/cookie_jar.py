# -*- coding: utf-8 -*-

import time
from datetime import timedelta


class CookieJar:
    def __init__(self, pluginname, account=None):
        self.cookies = {}
        self.plugin = pluginname
        self.account = account

    def add_cookies(self, clist):
        for c in clist:
            name = c.split("\t")[5]
            self.cookies[name] = c

    def get_cookies(self):
        return list(self.cookies.values())

    def parse_cookie(self, name):
        if name in self.cookies:
            return self.cookies[name].split("\t")[6]
        else:
            return None

    def get_cookie(self, name):
        return self.parse_cookie(name)

    def set_cookie(
        self,
        domain,
        name,
        value,
        path="/",
        exp=time.time() + timedelta(hours=744).seconds,  #: 31 days retention
    ):
        self.cookies[
            name
        ] = f".{domain}    TRUE    {path}    FALSE    {exp}    {name}    {value}"

    def clear(self):
        self.cookies = {}
