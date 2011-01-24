#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""

import pycurl

from urllib import quote, urlencode
from cStringIO import StringIO

from module.plugins.Plugin import Abort

def myquote(url):
        return quote(url, safe="%/:=&?~#+!$,;'@()*[]")

class BadHeader(Exception):
    def __init__(self, code):
        Exception.__init__(self, "Bad server response: %s"% code)
        self.code = code


class HTTPRequest():
    def __init__(self, cookies=None, interface=None, proxies=None):
        self.c = pycurl.Curl()
        self.rep = StringIO()

        self.cj = cookies #cookiejar

        self.lastURL = None
        self.lastEffectiveURL = None
        self.abort = False
        self.code = 0 # last http code

        self.header = ""

        self.initHandle()
        self.setInterface(interface, proxies)

        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)


    def initHandle(self):
        """ sets common options to curl handle """
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 5)
        self.c.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.c.setopt(pycurl.NOSIGNAL, 1)
        self.c.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, "AUTOREFERER"):
            self.c.setopt(pycurl.AUTOREFERER, 1)
        self.c.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.c.setopt(pycurl.LOW_SPEED_TIME, 30)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 5)

        #self.c.setopt(pycurl.VERBOSE, 1)

        self.c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.2.10) Gecko/20100916 Firefox/3.6.10")
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, "gzip, deflate")
        self.c.setopt(pycurl.HTTPHEADER, ["Accept: */*",
                            "Accept-Language: en-US,en",
                           "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                           "Connection: keep-alive",
                           "Keep-Alive: 300"])

    def setInterface(self, interface, proxy):
        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, str(interface))

        if proxy:
            if proxy["type"] == "socks4":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
            elif proxy["type"] == "socks5":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            else:
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            self.c.setopt(pycurl.PROXY, "%s:%s" % (proxy["address"], proxy["port"]))

            if proxy["username"]:
                self.c.setopt(pycurl.PROXYUSERPWD, "%s:%s" % (proxy["username"], proxy["password"]))

    def addCookies(self):
        """ put cookies from curl handle to cj """
        if self.cj:
            self.cj.addCookies(self.c.getinfo(pycurl.INFO_COOKIELIST))

    def getCookies(self):
        """ add cookies from cj to curl handle """
        if self.cj:
            for c in self.cj.getCookies():
                self.c.setopt(pycurl.COOKIELIST, c)
        return

    def clearCookies(self):
        self.c.setopt(pycurl.COOKIELIST, "")

    def setRequestContext(self, url, get, post, referer, cookies):
        """ sets everything needed for the request """

        url = myquote(str(url))

        if get:
            get = urlencode(get)
            url = "%s?%s" % (url, get)

        self.c.setopt(pycurl.URL, url)
        self.c.lastUrl = url

        if post:
            post = urlencode(post)
            self.c.setopt(pycurl.POSTFIELDS, post)

        if referer and self.lastURL:
            self.c.setopt(pycurl.REFERER, self.lastURL)

        if cookies:
            self.c.setopt(pycurl.COOKIEFILE, "")
            self.c.setopt(pycurl.COOKIEJAR, "")
            self.getCookies()


    def load(self, url, get={}, post={}, referer=True, cookies=True, just_header=False):
        """ load and returns a given page """

        self.setRequestContext(url, get, post, referer, cookies)

        self.header = ""

        #@TODO raw_cookies and some things in old backend, which are apperently not needed

        if just_header:
            self.c.setopt(pycurl.NOBODY, 1)
            self.c.perform()
            rep = self.header
        else:
            self.c.perform()
            rep = self.getResponse()

        self.code = self.verifyHeader()

        self.lastEffectiveURL = self.c.getinfo(pycurl.EFFECTIVE_URL)
        self.addCookies()

        return rep

    def verifyHeader(self):
        """ raise an exceptions on bad headers """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in range(400,404) or code in range(405,418) or code in range(500,506):
            #404 will NOT raise an exception
            raise BadHeader(code)
        return code

    def getResponse(self):
        """ retrieve response from string io """
        value = self.rep.getvalue()
        self.rep.close()
        self.rep = StringIO()
        return value

    def write(self, buf):
        """ writes response """
        if self.rep.tell() > 500000 or self.abort:
            rep = self.getResponse()
            if self.abort: raise Abort()
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)

    def writeHeader(self, buf):
        """ writes header """
        self.header += buf

    def close(self):
        """ cleanup, unusable after this """
        self.rep.close()
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "c"):
            self.c.close()
            del self.c


if __name__ == "__main__":
    url = "http://pyload.org"
    c = HTTPRequest()
    print c.load(url)
    