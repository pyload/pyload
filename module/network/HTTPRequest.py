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

def myquote(url):
        return quote(url, safe="%/:=&?~#+!$,;'@()*[]")

class HTTPRequest():
    def __init__(self, cookies=None, interface=None, proxies=None):
        self.c = pycurl.Curl()
        self.rep = StringIO()

        self.cj = cookies #cookiejar

        self.lastURL = None
        self.lastEffectiveURL = None
        self.abort = False

        self.header = ""

        self.initHandle()
        self.setInterface(interface, proxies)


    def initHandle(self):
        """ sets common options to curl handle """
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 5)
        self.c.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.c.setopt(pycurl.NOSIGNAL, 1)
        self.c.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, "AUTOREFERER"):
            self.c.setopt(pycurl.AUTOREFERER, 1)
        self.c.setopt(pycurl.BUFFERSIZE, 32 * 1024)
        self.c.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.c.setopt(pycurl.LOW_SPEED_TIME, 30)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 20)

        #self.c.setopt(pycurl.VERBOSE, 1)

        self.c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.2.10) Gecko/20100916 Firefox/3.6.10")
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, "gzip, deflate")
        self.c.setopt(pycurl.HTTPHEADER, ["Accept: */*",
                            "Accept-Language: en-US,en",
                           "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                           "Connection: keep-alive",
                           "Keep-Alive: 300"])

    def setInterface(self, interface, proxies):
        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, interface)

        #@TODO set proxies

    def addCookies(self):
        if self.cj:
            self.cj.addCookies(self.c.getinfo(pycurl.INFO_COOKIELIST))

    def getCookies(self):
        if self.cj:
            for c in self.cj.getCookies():
                self.c.setopt(pycurl.COOKIELIST, c)
        return

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


    def load(self, url, get={}, post={}, referer=True, cookies=True):
        """ load and returns a given page """

        self.setRequestContext(url, get, post, referer, cookies)

        self.header = ""
        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)
        #@TODO header_only, raw_cookies and some things in old backend, which are apperently not needed

        self.c.perform()

        self.lastEffectiveURL = self.c.getinfo(pycurl.EFFECTIVE_URL)
        self.addCookies()

        return self.getResponse()


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
        self.c.close()
        self.rep.close()
        if hasattr(self, "cj"):
            del self.cj


if __name__ == "__main__":
    url = "http://pyload.org"
    c = HTTPRequest()
    print c.load(url)
    