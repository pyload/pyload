# -*- coding: utf-8 -*-

from time import time
from Cookie import SimpleCookie


class CookieJar(SimpleCookie):

    def getCookie(self, name):
        return self[name].value

    def setCookie(self, domain, name, value, path="/", exp=None, secure="FALSE"):
        if not exp: exp = time() + 3600 * 24 * 180

        self[name] = value
        self[name]["domain"] = domain
        self[name]["path"] = path
        self[name]["expires"] = exp
        if secure == "TRUE":
            self[name]["secure"] = secure
