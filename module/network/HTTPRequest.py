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

import cStringIO
import pycurl

from codecs import getincrementaldecoder, lookup, BOM_UTF8
from urllib import quote, urlencode
from httplib import responses
from logging import getLogger

from module.plugins.Plugin import Abort

def myquote(url):
    return quote(url.encode('utf_8') if isinstance(url, unicode) else url, safe="%/:=&?~#+!$,;'@()*[]")
    
def myurlencode(data):
    data = dict(data)
    return urlencode(dict((x.encode('utf_8') if isinstance(x, unicode) else x, \
        y.encode('utf_8') if isinstance(y, unicode) else y ) for x, y in data.iteritems()))

bad_headers = range(400, 404) + range(405, 418) + range(500, 506)

unofficial_responses = {
    440: "Login Timeout - The client's session has expired and must log in again.",
    449: 'Retry With - The server cannot honour the request because the user has not provided the required information',
    451: 'Redirect - Unsupported Redirect Header',
    509: 'Bandwidth Limit Exceeded',
    520: 'Unknown Error',
    521: 'Web Server Is Down - The origin server has refused the connection from CloudFlare',
    522: 'Connection Timed Out - CloudFlare could not negotiate a TCP handshake with the origin server',
    523: 'Origin Is Unreachable - CloudFlare could not reach the origin server',
    524: 'A Timeout Occurred - CloudFlare did not receive a timely HTTP response',
    525: 'SSL Handshake Failed - CloudFlare could not negotiate a SSL/TLS handshake with the origin server',
    526: 'Invalid SSL Certificate - CloudFlare could not validate the SSL/TLS certificate that the origin server presented',
    527: 'Railgun Error - CloudFlare requests timeout or failed after the WAN connection has been established',
    530: 'Site Is Frozen - Used by the Pantheon web platform to indicate a site that has been frozen due to inactivity'}

class BadHeader(Exception):
    def __init__(self, code, header="", content=""):
        int_code = int(code)
        Exception.__init__(self, "Bad server response: %s %s" %
                           (code, responses.get(int_code, unofficial_responses.get(int_code, "unknown error code"))))
        self.code = int_code
        self.header = header
        self.content = content


class HTTPRequest():
    def __init__(self, cookies=None, options=None):
        self.c = pycurl.Curl()
        self.rep = None

        self.cj = cookies #cookiejar

        self.lastURL = None
        self.lastEffectiveURL = None
        self.abort = False
        self.code = 0 # last http code

        self.header = ""

        self.headers = [] #temporary request header

        self.initHandle()
        self.setInterface(options)

        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)

        self.log = getLogger("log")


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

        self.c.setopt(pycurl.USERAGENT,
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0")
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, "gzip, deflate")
        self.c.setopt(pycurl.HTTPHEADER, ["Accept: */*",
                                          "Accept-Language: en-US,en",
                                          "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                                          "Connection: keep-alive",
                                          "Keep-Alive: 300",
                                          "Expect:"])

    def setInterface(self, options):

        interface, proxy, ipv6 = options["interface"], options["proxies"], options["ipv6"]

        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, str(interface))

        if proxy:
            if proxy["type"] == "socks4":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
            elif proxy["type"] == "socks5":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            else:
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            self.c.setopt(pycurl.PROXY, str(proxy["address"]))
            self.c.setopt(pycurl.PROXYPORT, proxy["port"])

            if proxy["username"]:
                self.c.setopt(pycurl.PROXYUSERPWD, str("%s:%s" % (proxy["username"], proxy["password"])))

        if ipv6:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
        else:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        if "auth" in options:
            self.c.setopt(pycurl.USERPWD, str(options["auth"]))

        if "timeout" in options:
            self.c.setopt(pycurl.LOW_SPEED_TIME, options["timeout"])


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

    def setRequestContext(self, url, get, post, referer, cookies, multipart=False):
        """ sets everything needed for the request """

        self.rep = cStringIO.StringIO()

        url = myquote(url)

        if get:
            get = urlencode(get)
            url = "%s?%s" % (url, get)

        self.c.setopt(pycurl.URL, url)
        self.c.lastUrl = url

        if post:
            self.c.setopt(pycurl.POST, 1)
            if not multipart:
                if type(post) == unicode:
                    post = str(post) #unicode not allowed
                elif type(post) == str:
                    pass
                else:
                    post = myurlencode(post)

                self.c.setopt(pycurl.POSTFIELDS, post)
            else:
                post = [(x, y.encode('utf8') if type(y) == unicode else y ) for x, y in post.iteritems()]
                self.c.setopt(pycurl.HTTPPOST, post)
        else:
            self.c.setopt(pycurl.POST, 0)

        if referer and self.lastURL:
            self.c.setopt(pycurl.REFERER, str(self.lastURL))

        if cookies:
            self.c.setopt(pycurl.COOKIEFILE, "")
            self.c.setopt(pycurl.COOKIEJAR, "")
            self.getCookies()


    def load(self, url, get={}, post={}, referer=True, cookies=True, just_header=False, multipart=False, decode=False):
        """ load and returns a given page """

        self.setRequestContext(url, get, post, referer, cookies, multipart)

        self.header = ""

        self.c.setopt(pycurl.HTTPHEADER, self.headers)

        if just_header:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.c.setopt(pycurl.NOBODY, 1)
            self.c.perform()
            rep = self.header

            self.c.setopt(pycurl.FOLLOWLOCATION, 1)
            self.c.setopt(pycurl.NOBODY, 0)

        else:
            self.c.perform()
            rep = self.getResponse()

        self.c.setopt(pycurl.POSTFIELDS, "")
        self.lastEffectiveURL = self.c.getinfo(pycurl.EFFECTIVE_URL)

        self.addCookies()

        try:
            self.code = self.verifyHeader()

        finally:
            self.rep.close()
            self.rep = None

        if decode:
            rep = self.decodeResponse(rep)

        return rep

    def verifyHeader(self):
        """ raise an exceptions on bad headers """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in bad_headers:
            #404 will NOT raise an exception
            raise BadHeader(code, self.header, self.getResponse())
        return code

    def checkHeader(self):
        """ check if header indicates failure"""
        return int(self.c.getinfo(pycurl.RESPONSE_CODE)) not in bad_headers

    def getResponse(self):
        """ retrieve response from string io """
        if self.rep is None:
            return ""

        else:
            return self.rep.getvalue()

    def decodeResponse(self, rep):
        """ decode with correct encoding, relies on header """
        header = self.header.splitlines()
        encoding = "utf8" # default encoding

        for line in header:
            line = line.lower().replace(" ", "")
            if not line.startswith("content-type:") or\
               ("text" not in line and "application" not in line):
                continue

            none, delemiter, charset = line.rpartition("charset=")
            if delemiter:
                charset = charset.split(";")
                if charset:
                    encoding = charset[0]

        try:
            #self.log.debug("Decoded %s" % encoding )
            if lookup(encoding).name == 'utf-8' and rep.startswith(BOM_UTF8):
                encoding = 'utf-8-sig'
            
            decoder = getincrementaldecoder(encoding)("replace")
            rep = decoder.decode(rep, True)

            #TODO: html_unescape as default

        except LookupError:
            self.log.debug("No Decoder foung for %s" % encoding)
        except Exception:
            self.log.debug("Error when decoding string from %s." % encoding)

        return rep

    def write(self, buf):
        """ writes response """
        if self.rep.tell() > 1000000 or self.abort:
            rep = self.getResponse()
            if self.abort:
                raise Abort()
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)

    def writeHeader(self, buf):
        """ writes header """
        self.header += buf

    def putHeader(self, name, value):
        self.headers.append("%s: %s" % (name, value))

    def clearHeaders(self):
        self.headers = []

    def close(self):
        """ cleanup, unusable after this """
        if self.rep:
            self.rep.close()
            del self.rep

        if hasattr(self, "cj"):
            del self.cj

        if hasattr(self, "c"):
            self.c.close()
            del self.c

if __name__ == "__main__":
    url = "http://pyload.org"
    c = HTTPRequest()
    print c.load(url)
    
