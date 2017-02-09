# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import print_function, unicode_literals

from builtins import bytes, range, str
from codecs import BOM_UTF8, getincrementaldecoder, lookup
from io import StringIO
from urllib.parse import quote, urlencode

from future import standard_library
from http.client import responses

import pycurl
from pyload.network.cookie import CookieJar
from pyload.plugin import Abort
from pyload.plugin.request import Request, ResponseException

standard_library.install_aliases()





def myquote(url):
    return quote(url.encode('utf8') if isinstance(url, str) else url, safe="%/:=&?~#+!$,;'@()*[]")


def myurlencode(data):
    data = dict(data)
    return urlencode(
        dict((x.encode('utf8') if isinstance(x, str) else x, y.encode('utf8') if isinstance(y, str) else y)
             for x, y in data.items()))


bad_headers = list(range(400, 418)) + list(range(500, 506))

pycurl.global_init(pycurl.GLOBAL_DEFAULT)


class CurlRequest(Request):
    """
    Request class based on libcurl.
    """
    __version__ = "0.1"

    CONTEXT_CLASS = CookieJar

    def __init__(self, *args, **kwargs):
        self.c = pycurl.Curl()
        Request.__init__(self, *args, **kwargs)

        self.rep = StringIO()
        self.last_url = None
        self.last_effective_url = None
        self.header = ""

        # cookiejar defines the context
        self.cj = self.context

        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.write_header)

    # TODO: addHeader

    @property
    def http(self):
        print("Deprecated usage of req.http, just use req instead")
        return self

    def init_context(self):
        self.init_handle()

        if self.config:
            self.set_interface(self.config)
            self.init_options(self.config)

    def init_handle(self):
        """
        Sets common options to curl handle.
        """
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 5)
        self.c.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.c.setopt(pycurl.NOSIGNAL, 1)
        self.c.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, "AUTOREFERER"):
            self.c.setopt(pycurl.AUTOREFERER, 1)
        self.c.setopt(pycurl.SSL_VERIFYPEER, 0)
        # Interval for low speed, detects connection loss, but can abort dl if
        # hoster stalls the download
        self.c.setopt(pycurl.LOW_SPEED_TIME, 45)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 5)

        # do not save the cookies
        self.c.setopt(pycurl.COOKIEFILE, b"")
        self.c.setopt(pycurl.COOKIEJAR, b"")

        # self.c.setopt(pycurl.VERBOSE, 1)

        self.c.setopt(pycurl.USERAGENT,
                      "Mozilla/5.0 (Windows NT 6.1; Win64; x64;en; rv:5.0) Gecko/20110619 Firefox/5.0")
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, b"gzip, deflate")

        self.headers.update(
            {"Accept": "*/*",
             "Accept-Language": "en-US,en",
             "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
             "Connection": "keep-alive",
             "Keep-Alive": "300",
             "Expect": ""})

    def set_interface(self, options):

        interface, proxy, ipv6 = options[
            'interface'], options['proxies'], options['ipv6']

        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, bytes(interface))

        if proxy:
            if proxy['type'] == "socks4":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
            elif proxy['type'] == "socks5":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            else:
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            self.c.setopt(pycurl.PROXY, bytes(proxy['host']))
            self.c.setopt(pycurl.PROXYPORT, proxy['port'])

            if proxy['username']:
                self.c.setopt(pycurl.PROXYUSERPWD, bytes(
                    "{}:{}".format(proxy['username'], proxy['password'])))

        if ipv6:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
        else:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        if "timeout" in options:
            self.c.setopt(pycurl.LOW_SPEED_TIME, options['timeout'])

        if "auth" in options:
            self.c.setopt(pycurl.USERPWD, bytes(options['auth']))

    def init_options(self, options):
        """
        Sets same options as available in pycurl.
        """
        for k, v in options.items():
            if hasattr(pycurl, k):
                self.c.setopt(getattr(pycurl, k), v)

    def set_request_context(self, url, get, post, referer, cookies, multipart=False):
        """
        Sets everything needed for the request.
        """
        url = myquote(url)

        if get:
            get = urlencode(get)
            url = "{}?{}".format(url, get)

        self.c.setopt(pycurl.URL, url)

        if post:
            self.c.setopt(pycurl.POST, 1)
            if not multipart:
                if isinstance(post, str):
                    post = str(post)  # unicode not allowed
                elif isinstance(post, str):
                    pass
                else:
                    post = myurlencode(post)

                self.c.setopt(pycurl.POSTFIELDS, post)
            else:
                post = [(x, y.encode('utf8') if isinstance(y, str) else y)
                        for x, y in post.items()]
                self.c.setopt(pycurl.HTTPPOST, post)
        else:
            self.c.setopt(pycurl.POST, 0)

        if referer and self.last_url:
            self.headers['Referer'] = str(self.last_url)
        else:
            self.headers['Referer'] = ""

        if cookies:
            for c in self.cj.output().splitlines():
                self.c.setopt(pycurl.COOKIELIST, c)
        else:
            # Magic string that erases all cookies
            self.c.setopt(pycurl.COOKIELIST, b"ALL")

        # TODO: remove auth again
        if "auth" in self.options:
            self.c.setopt(pycurl.USERPWD, bytes(self.options['auth']))

        self.c.setopt(pycurl.HTTPHEADER, self.headers.to_headerlist())

    def load(self, url, get={}, post={}, referer=True, cookies=True, just_header=False, multipart=False, decode=False):
        """
        Load and returns a given page.
        """
        self.set_request_context(url, get, post, referer, cookies, multipart)

        # TODO: use http/rfc message instead
        self.header = ""

        if "header" in self.options:
            # TODO
            print("custom header not implemented")
            self.c.setopt(pycurl.HTTPHEADER, self.options['header'])

        if just_header:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.c.setopt(pycurl.NOBODY, 1)  # TODO: nobody= no post?

            # overwrite HEAD request, we want a common request type
            if post:
                self.c.setopt(pycurl.CUSTOMREQUEST, b"POST")
            else:
                self.c.setopt(pycurl.CUSTOMREQUEST, b"GET")

            try:
                self.c.perform()
                rep = self.header
            finally:
                self.c.setopt(pycurl.FOLLOWLOCATION, 1)
                self.c.setopt(pycurl.NOBODY, 0)
                self.c.unsetopt(pycurl.CUSTOMREQUEST)

        else:
            self.c.perform()
            rep = self.get_response()

        self.c.setopt(pycurl.POSTFIELDS, b"")
        self.last_url = myquote(url)
        self.last_effective_url = self.c.getinfo(pycurl.EFFECTIVE_URL)
        if self.last_effective_url:
            self.last_url = self.last_effective_url
        self.code = self.verify_header()

        if cookies:
            self.parse_cookies()

        if decode:
            rep = self.decode_response(rep)

        return rep

    def parse_cookies(self):
        for c in self.c.getinfo(pycurl.INFO_COOKIELIST):
            # http://xiix.wordpress.com/2006/03/23/mozillafirefox-cookie-format
            domain, flag, path, secure, expires, name, value = c.split("\t")
            # http only was added in py 2.6
            domain = domain.replace("#HttpOnly_", "")
            self.cj.set_cookie(domain, name, value, path, expires, secure)

    def verify_header(self):
        """
        Raise an exceptions on bad headers.
        """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in bad_headers:
            raise ResponseException(
                code, responses.get(code, "Unknown statuscode"))
        return code

    def get_response(self):
        """
        Retrieve response from string io.
        """
        if self.rep is None:
            return ""
        value = self.rep.getvalue()
        self.rep.close()
        self.rep = StringIO()
        return value

    def decode_response(self, rep):
        """
        Decode with correct encoding, relies on header.
        """
        header = self.header.splitlines()
        encoding = "utf8"  # default encoding

        for line in header:
            line = line.lower().replace(" ", "")
            if (not line.startswith("content-type:") or
                    ("text" not in line and "application" not in line)):
                continue

            none, delemiter, charset = line.rpartition("charset=")
            if delemiter:
                charset = charset.split(";")
                if charset:
                    encoding = charset[0]

        try:
            #self.pyload.log.debug("Decoded {}".format(encoding))
            if lookup(encoding).name == 'utf-8' and rep.startswith(BOM_UTF8):
                encoding = 'utf-8-sig'

            decoder = getincrementaldecoder(encoding)("replace")
            rep = decoder.decode(rep, True)

            # TODO: html_unescape as default

        except LookupError:
            self.pyload.log.debug("No Decoder found for {}".format(encoding))
        except Exception:
            self.pyload.log.debug(
                "Error when decoding string from {}".format(encoding))

        return rep

    def write(self, buf):
        """
        Writes response.
        """
        if self.rep.tell() > 1000000 or self.do_abort:
            rep = self.get_response()
            if self.do_abort:
                raise Abort
            with open("response.dump", "wb") as f:
                f.write(rep)
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)

    def write_header(self, buf):
        """
        Writes header.
        """
        self.header += buf

    def reset(self):
        self.cj.clear()
        self.options.clear()

    def close(self):
        """
        Cleanup, unusable after this.
        """
        self.rep.close()
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "c"):
            self.c.close()
            del self.c
