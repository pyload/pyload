# -*- coding: utf-8 -*-

import time
from datetime import timedelta


class CookieJar:
    def __init__(self, pluginname, account=None):
        self.cookies = {}
        self.plugin = pluginname
        self.account = account

    def set_cookies(self, cookie_list):
        """
        Add cookies to the jar.

        Each item in cookie_list may be either:
        - a str in Netscape cookie file format: "domain<TAB>flag<TAB>path<TAB>secure<TAB>expires<TAB>name<TAB>value"
        - a tuple (domain, name, value); it is converted into a cookie via set_cookie() with default path="/"
          and expiration set to now + 31 days.
        """
        for cookie in cookie_list:
            if isinstance(cookie, str):
                name = cookie.split("\t")[5]
                self.cookies[name] = cookie

            elif isinstance(cookie, tuple) and len(cookie) == 3:
                self.set_cookie(*cookie)

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
        exp=time.time() + timedelta(days=31).total_seconds(),  #: 31 days retention
    ):
        self.cookies[
            name
        ] = f".{domain}\tTRUE\t{path}\tFALSE\t{exp}\t{name}\t{value}"

    def clear(self):
        self.cookies = {}
