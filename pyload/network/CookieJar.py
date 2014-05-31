# -*- coding: utf-8 -*-

from time import time
from Cookie import SimpleCookie

class CookieJar(SimpleCookie):

    def getCookie(self, name):
        return self[name].value

    def setCookie(self, domain, name, value, path="/", exp=None, secure="FALSE"):
        self[name] = value
        self[name]["domain"] = domain
        self[name]["path"] = path
        
        #Value of expires should be integer if possible
        # otherwise the cookie won't be used
        expire=0
        if not exp:
	        expires = time() + 3600 * 24 * 180
        else:
            try:
                expires = int(exp)
            except ValueError:
                expires = exp
        
        self[name]["expires"] = expires
        if secure == "TRUE":
            self[name]["secure"] = secure
