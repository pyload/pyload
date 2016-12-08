# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
import pycurl

from codecs import getincrementaldecoder, lookup, BOM_UTF8
from urllib.parse import quote, urlencode
from http.client import responses
from io import StringIO

from pyload.plugins.base import Abort
from pyload.network.cookiejar import CookieJar

from ..request import Request, ResponseException


def myquote(url):
    return quote(url.encode('utf8') if isinstance(url, str) else url, safe="%/:=&?~#+!$,;'@()*[]")


def myurlencode(data):
    data = dict(data)
    return urlencode(dict((x.encode('utf8') if isinstance(x, str) else x, \
                           y.encode('utf8') if isinstance(y, str) else y) for x, y in data.items()))


bad_headers = range(400, 418) + range(500, 506)

pycurl.global_init(pycurl.GLOBAL_DEFAULT)


class CurlRequest(Request):
    """  Request class based on libcurl """

    __version__ = "0.1"

    CONTEXT_CLASS = CookieJar

    def __init__(self, *args, **kwargs):
        self.c = pycurl.Curl()
        Request.__init__(self, *args, **kwargs)

        self.rep = StringIO()
        self.lastURL = None
        self.lastEffectiveURL = None
        self.header = ""

        # cookiejar defines the context
        self.cj = self.context

        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)

    # TODO: addHeader

    @property
    def http(self):
        print("Deprecated usage of req.http, just use req instead")
        return self

    def initContext(self):
        self.initHandle()

        if self.config:
            self.setInterface(self.config)
            self.initOptions(self.config)

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
        # Interval for low speed, detects connection loss, but can abort dl if hoster stalls the download
        self.c.setopt(pycurl.LOW_SPEED_TIME, 45)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 5)

        # don't save the cookies
        self.c.setopt(pycurl.COOKIEFILE, "")
        self.c.setopt(pycurl.COOKIEJAR, "")

        # self.c.setopt(pycurl.VERBOSE, 1)

        self.c.setopt(pycurl.USERAGENT,
                      "Mozilla/5.0 (Windows NT 6.1; Win64; x64;en; rv:5.0) Gecko/20110619 Firefox/5.0")
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, "gzip, deflate")

        self.headers.update(
            {"Accept": "*/*",
             "Accept-Language": "en-US,en",
             "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
             "Connection": "keep-alive",
             "Keep-Alive": "300",
             "Expect": ""})

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

        if "timeout" in options:
            self.c.setopt(pycurl.LOW_SPEED_TIME, options["timeout"])

        if "auth" in options:
            self.c.setopt(pycurl.USERPWD, str(options["auth"]))

    def initOptions(self, options):
        """  Sets same options as available in pycurl  """
        for k, v in options.items():
            if hasattr(pycurl, k):
                self.c.setopt(getattr(pycurl, k), v)

    def setRequestContext(self, url, get, post, referer, cookies, multipart=False):
        """ sets everything needed for the request """
        url = myquote(url)

        if get:
            get = urlencode(get)
            url = "%s?%s" % (url, get)

        self.c.setopt(pycurl.URL, url)

        if post:
            self.c.setopt(pycurl.POST, 1)
            if not multipart:
                if isinstance(post, str):
                    post = str(post) #unicode not allowed
                elif isinstance(post, str):
                    pass
                else:
                    post = myurlencode(post)

                self.c.setopt(pycurl.POSTFIELDS, post)
            else:
                post = [(x, y.encode('utf8') if isinstance(y, str) else y) for x, y in post.items()]
                self.c.setopt(pycurl.HTTPPOST, post)
        else:
            self.c.setopt(pycurl.POST, 0)

        if referer and self.lastURL:
            self.headers["Referer"] = str(self.lastURL)
        else:
            self.headers["Referer"] = ""

        if cookies:
            for c in self.cj.output().splitlines():
                self.c.setopt(pycurl.COOKIELIST, c)
        else:
            # Magic string that erases all cookies
            self.c.setopt(pycurl.COOKIELIST, "ALL")

        # TODO: remove auth again
        if "auth" in self.options:
            self.c.setopt(pycurl.USERPWD, str(self.options["auth"]))

        self.c.setopt(pycurl.HTTPHEADER, self.headers.to_headerlist())

    def load(self, url, get={}, post={}, referer=True, cookies=True, just_header=False, multipart=False, decode=False):
        """ load and returns a given page """

        self.setRequestContext(url, get, post, referer, cookies, multipart)

        # TODO: use http/rfc message instead
        self.header = ""

        if "header" in self.options:
            # TODO
            print("custom header not implemented")
            self.c.setopt(pycurl.HTTPHEADER, self.options["header"])

        if just_header:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.c.setopt(pycurl.NOBODY, 1) #TODO: nobody= no post?

            # overwrite HEAD request, we want a common request type
            if post:
                self.c.setopt(pycurl.CUSTOMREQUEST, "POST")
            else:
                self.c.setopt(pycurl.CUSTOMREQUEST, "GET")

            try:
                self.c.perform()
                rep = self.header
            finally:
                self.c.setopt(pycurl.FOLLOWLOCATION, 1)
                self.c.setopt(pycurl.NOBODY, 0)
                self.c.unsetopt(pycurl.CUSTOMREQUEST)

        else:
            self.c.perform()
            rep = self.getResponse()

        self.c.setopt(pycurl.POSTFIELDS, "")
        self.lastURL = myquote(url)
        self.lastEffectiveURL = self.c.getinfo(pycurl.EFFECTIVE_URL)
        if self.lastEffectiveURL:
            self.lastURL = self.lastEffectiveURL
        self.code = self.verifyHeader()

        if cookies:
            self.parseCookies()

        if decode:
            rep = self.decodeResponse(rep)

        return rep

    def parseCookies(self):
        for c in self.c.getinfo(pycurl.INFO_COOKIELIST):
            #http://xiix.wordpress.com/2006/03/23/mozillafirefox-cookie-format
            domain, flag, path, secure, expires, name, value = c.split("\t")
            # http only was added in py 2.6
            domain = domain.replace("#HttpOnly_", "")
            self.cj.setCookie(domain, name, value, path, expires, secure)

    def verifyHeader(self):
        """ raise an exceptions on bad headers """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in bad_headers:
            raise ResponseException(code, responses.get(code, "Unknown statuscode"))
        return code

    def getResponse(self):
        """ retrieve response from string io """
        if self.rep is None: return ""
        value = self.rep.getvalue()
        self.rep.close()
        self.rep = StringIO()
        return value

    def decodeResponse(self, rep):
        """ decode with correct encoding, relies on header """
        header = self.header.splitlines()
        encoding = "utf8" # default encoding

        for line in header:
            line = line.lower().replace(" ", "")
            if not line.startswith("content-type:") or \
                    ("text" not in line and "application" not in line):
                continue

            none, delemiter, charset = line.rpartition("charset=")
            if delemiter:
                charset = charset.split(";")
                if charset:
                    encoding = charset[0]

        try:
            #self.log.debug("Decoded %s" % encoding)
            if lookup(encoding).name == 'utf-8' and rep.startswith(BOM_UTF8):
                encoding = 'utf-8-sig'

            decoder = getincrementaldecoder(encoding)("replace")
            rep = decoder.decode(rep, True)

            #TODO: html_unescape as default

        except LookupError:
            self.log.debug("No Decoder found for %s" % encoding)
        except Exception:
            self.log.debug("Error when decoding string from %s." % encoding)

        return rep

    def write(self, buf):
        """ writes response """
        if self.rep.tell() > 1000000 or self.doAbort:
            rep = self.getResponse()
            if self.doAbort: raise Abort
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)

    def writeHeader(self, buf):
        """ writes header """
        self.header += buf

    def reset(self):
        self.cj.clear()
        self.options.clear()

    def close(self):
        """ cleanup, unusable after this """
        self.rep.close()
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "c"):
            self.c.close()
            del self.c
