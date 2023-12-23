# -*- coding: utf-8 -*-

import codecs
import io
import mimetypes
import os
from itertools import chain
from logging import getLogger
from urllib.parse import quote, urlencode

import certifi
import pycurl

from pyload import APPID

from ...utils.check import is_mapping
from ...utils.convert import to_bytes, to_str
from ..exceptions import Abort
from .exceptions import BadHeader

if not hasattr(pycurl, "PROXYTYPE_HTTPS"):
    pycurl.PROXYTYPE_HTTPS = 2


def myquote(url):
    try:
        url = url.encode()
    except AttributeError:
        pass
    return quote(url, safe="%/:=&?~#+!$,;'@()*[]")


def myurlencode(data):
    data = dict(data)
    return urlencode(
        {
            x.encode()
            if hasattr(x, "encode")
            else x: y.encode()
            if hasattr(y, "encode")
            else y
            for x, y in data.items()
        }
    )


BAD_STATUS_CODES = tuple(
    chain(range(400, 404), range(405, 418), range(500, 506))
)


class FormFile:
    def __init__(self, filename, data=None, mimetype=None):
        self.filename = os.path.abspath(filename)
        self.data = data
        self.mimetype = (
            mimetype or mimetypes.guess_type(filename)[0]
            if not data and os.path.exists(filename)
            else "application/octet-stream"
        )

    def __repr__(self):
        return f"FormFile <'{os.path.basename(self.filename)}'>"


class HTTPRequest:
    def __init__(self, cookies=None, options=None, limit=2_000_000):
        self.exception = None
        self.limit = limit

        self.c = pycurl.Curl()
        self.rep = None

        self.cj = cookies  #: cookiejar

        self.last_url = None
        self.last_effective_url = None
        self.code = 0  #: last http code

        self.response_header = b""

        self.request_headers = []  #: temporary request header

        self.abort = False
        self.decode = False

        self.init_handle()
        self.set_interface(options)

        self.c.setopt(pycurl.WRITEFUNCTION, self.write_body)
        self.c.setopt(pycurl.HEADERFUNCTION, self.write_header)

        self.log = getLogger(APPID)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def init_handle(self):
        """
        sets common options to curl handle.
        """
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 10)
        self.c.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.c.setopt(pycurl.NOSIGNAL, 1)
        self.c.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, "AUTOREFERER"):
            self.c.setopt(pycurl.AUTOREFERER, 1)
        self.c.setopt(pycurl.SSL_VERIFYPEER, 1)
        self.c.setopt(pycurl.LOW_SPEED_TIME, 60)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 5)
        if hasattr(pycurl, "USE_SSL"):
            self.c.setopt(pycurl.USE_SSL, pycurl.USESSL_TRY)

        # self.c.setopt(pycurl.VERBOSE, 1)
        # self.c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)

        self.c.setopt(
            pycurl.USERAGENT,
            b"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        )
        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, b"gzip, deflate")

        self.c.setopt(
            pycurl.HTTPHEADER,
            [
                b"Accept: */*",
                b"Accept-Language: en-US,en",
                b"Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                b"Connection: keep-alive",
                b"Keep-Alive: 300",
                b"Expect:",
            ],
        )

    def set_interface(self, options):
        options = {
            k: v.encode() if hasattr(v, "encode") else v for k, v in options.items()
        }

        interface, proxy, ipv6 = (
            options["interface"],
            options["proxies"],
            options["ipv6"],
        )

        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, interface)

        if proxy:
            if proxy["type"] == "http":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
            elif proxy["type"] == "https":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTPS)
                self.c.setopt(pycurl.PROXY_SSL_VERIFYPEER, 0)
            elif proxy["type"] == "socks4":
                self.c.setopt(
                    pycurl.PROXYTYPE,
                    pycurl.PROXYTYPE_SOCKS4A if proxy["socks_resolve_dns"] else pycurl.PROXYTYPE_SOCKS4
                )
            elif proxy["type"] == "socks5":
                self.c.setopt(
                    pycurl.PROXYTYPE,
                    pycurl.PROXYTYPE_SOCKS5_HOSTNAME if proxy["socks_resolve_dns"] else pycurl.PROXYTYPE_SOCKS5
                )

            self.c.setopt(pycurl.PROXY, proxy["host"])
            self.c.setopt(pycurl.PROXYPORT, int(proxy["port"]))

            if proxy["username"]:
                user = proxy["username"]
                pw = proxy["password"]
                self.c.setopt(pycurl.PROXYUSERPWD, f"{user}:{pw}".encode())

        if ipv6:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
        else:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        if "auth" in options:
            self.c.setopt(pycurl.USERPWD, options["auth"])

        if "timeout" in options:
            self.c.setopt(pycurl.LOW_SPEED_TIME, int(options["timeout"]))

        if "ssl_verify" in options:
            if options["ssl_verify"]:
                self.c.setopt(pycurl.CAINFO, certifi.where())
                ssl_verify = 1
            else:
                ssl_verify = 0

            self.c.setopt(pycurl.SSL_VERIFYPEER, ssl_verify)

    def add_cookies(self):
        """
        put cookies from curl handle to cj.
        """
        if self.cj:
            self.cj.add_cookies(self.c.getinfo(pycurl.INFO_COOKIELIST))

    def get_cookies(self):
        """
        add cookies from cj to curl handle.
        """
        if self.cj:
            for c in self.cj.get_cookies():
                self.c.setopt(pycurl.COOKIELIST, c)
        return

    def clear_cookies(self):
        self.c.setopt(pycurl.COOKIELIST, "")

    def set_request_context(self, url, get, post, referer, cookies, multipart=False, decode=True):
        """
        sets everything needed for the request.
        """
        self.rep = io.BytesIO()

        self.exception = None

        self.decode = decode

        url = myquote(url)

        if get:
            get = urlencode(get)
            url = f"{url}?{get}"

        self.c.setopt(pycurl.URL, url)
        self.c.last_url = url

        if post:
            self.c.setopt(pycurl.POST, 1)
            if not multipart:
                if post is True:
                    post = b""
                elif isinstance(post, str):
                    post = post.encode()
                elif is_mapping(post):
                    post = myurlencode(post)
                else:
                    raise ValueError("Invalid value for 'post'")

                self.c.setopt(pycurl.POSTFIELDS, post)

            else:
                multipart_post = []
                for k, v in post.items():
                    if isinstance(v, (str, bool, int)):
                        multipart_post.append((k, to_str(v)))

                    elif isinstance(v, FormFile):
                        filename = os.path.basename(v.filename).encode("utf8")
                        data = v.data
                        if data is None:
                            if not os.path.exists(v.filename):
                                continue
                            else:
                                with open(v.filename, "rb") as f:
                                    data = f.read()

                        else:
                            data = to_bytes(data)

                        multipart_post.append((k, (pycurl.FORM_BUFFER, filename,
                                                   pycurl.FORM_BUFFERPTR, data,
                                                   pycurl.FORM_CONTENTTYPE, v.mimetype)))

                self.c.setopt(pycurl.HTTPPOST, multipart_post)

        else:
            self.c.setopt(pycurl.POST, 0)
            self.c.setopt(pycurl.HTTPGET, 1)

        if referer and self.last_url:
            self.c.setopt(pycurl.REFERER, to_bytes(self.last_url))

        if cookies:
            self.c.setopt(pycurl.COOKIEFILE, b"")
            self.c.setopt(pycurl.COOKIEJAR, b"")
            self.get_cookies()

    def load(
        self,
        url,
        get={},
        post={},
        referer=True,
        cookies=True,
        just_header=False,
        multipart=False,
        decode=True,
        follow_location=True,
        save_cookies=True,
    ):
        """
        load and returns a given page.
        """
        self.set_request_context(url, get, post, referer, cookies, multipart, decode)

        self.response_header = b""

        self.c.setopt(pycurl.HTTPHEADER, self.request_headers)

        if not follow_location:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 1)

        try:
            self.c.perform()
        except pycurl.error as exc:
            if exc.args[0] == pycurl.E_WRITE_ERROR and self.exception:
                raise self.exception from None
            else:
                raise

        if not follow_location:
            self.c.setopt(pycurl.FOLLOWLOCATION, 1)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 0)

        self.c.setopt(pycurl.POSTFIELDS, b"")
        self.last_effective_url = self.c.getinfo(pycurl.EFFECTIVE_URL)

        if save_cookies:
            self.add_cookies()

        self.code = self.verify_header()

        ret = self.response_header if just_header else self.get_response()

        if decode:
            ret = (
                to_str(ret, encoding="iso-8859-1")
                if just_header
                else self.decode_response(ret)
            )

        self.rep.close()
        self.rep = None

        return ret

    def verify_header(self):
        """
        raise an exceptions on bad headers.
        """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in BAD_STATUS_CODES:
            response = self.decode_response(self.get_response()) if self.decode else self.get_response()
            header = to_str(self.response_header, encoding="iso-8859-1") if self.decode else self.response_header
            self.rep.close()
            self.rep = None

            # 404 will NOT raise an exception
            raise BadHeader(code, header, response)

        return code

    def check_header(self):
        """
        check if header indicates failure.
        """
        return int(self.c.getinfo(pycurl.RESPONSE_CODE)) not in BAD_STATUS_CODES

    def get_response(self):
        """
        retrieve response from bytes io.
        """
        if self.rep is None:
            return b""
        else:
            return self.rep.getvalue()

    def decode_response(self, response):
        """
        decode with correct encoding, relies on header.
        """
        header = self.response_header.splitlines()
        encoding = "utf-8"  #: default encoding

        for line in header:
            line = line.lower().replace(b" ", b"")
            if not line.startswith(b"content-type:") or (b"text" not in line and b"application" not in line):
                continue

            none, delimiter, charset = line.rpartition(b"charset=")
            if delimiter:
                charset = charset.split(b";")
                if charset:
                    encoding = to_str(charset[0])

        try:
            # self.log.debug(f"Decoded {encoding}")
            if codecs.lookup(encoding).name == "utf-8" and response.startswith(
                codecs.BOM_UTF8
            ):
                encoding = "utf-8-sig"

            decoder = codecs.getincrementaldecoder(encoding)("replace")
            response = decoder.decode(response, True)

            # TODO: html_unescape as default

        except LookupError:
            self.log.debug(f"No Decoder found for {encoding}")

        except Exception:
            self.log.debug(f"Error when decoding string from {encoding}", exc_info=True)

        return response

    def write_body(self, buf):
        """
        writes response.
        """
        if self.abort:
            self.exception = Abort()
            return pycurl.E_WRITE_ERROR

        elif self.limit and self.rep.tell() > self.limit:
            rep = self.get_response()
            with open("response.dump", mode="wb") as fp:
                fp.write(rep)

            self.exception = Exception(f"Loaded URL exceeded limit ({self.limit})")
            return pycurl.E_WRITE_ERROR

        self.rep.write(buf)
        return None  #: Everything is OK, please continue

    def write_header(self, buf):
        """
        writes header.
        """
        self.response_header += buf

    def put_header(self, name, value):
        self.request_headers.append(f"{name}: {value}")

    def clear_headers(self):
        self.request_headers = []

    def close(self):
        """
        cleanup, unusable after this.
        """
        if self.rep:
            self.rep.close()
            del self.rep

        if hasattr(self, "cj"):
            del self.cj

        if hasattr(self, "c"):
            self.c.close()
            del self.c
