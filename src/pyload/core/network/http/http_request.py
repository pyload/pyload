# -*- coding: utf-8 -*-

import codecs
import io
import mimetypes
import os
import tempfile
from itertools import chain
from logging import getLogger
from urllib.parse import quote, urlencode

import certifi
import pycurl
from aia_chaser import AiaChaser
from cryptography.hazmat.primitives.serialization import Encoding

from pyload import APPID

from ...utils.check import is_mapping
from ...utils.convert import to_bytes, to_str
from ...utils.web.parse import http_header as parse_header_line
from ...utils.web.purge import unescape as html_unescape
from ..exceptions import Abort
from .exceptions import BadHeader
from .http_headers import HttpHeaders

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

        self.cj = cookies  #: cookiejar

        self.last_url = None
        self.last_effective_url = None
        self.code = 0  #: last http code

        self._header_buffer = b""
        self._body_buffer = None

        self.request_headers = HttpHeaders()
        self.response_headers = HttpHeaders()

        self.abort = False
        self.decode = False

        self.ssl_aiachaser = False
        self.aia_cainfo = None

        self.init_handle()
        self.set_interface(options)
        self.default_max_redirect = max(options.get("max_redirect", 10), 0) or 5

        self.c.setopt(pycurl.WRITEFUNCTION, self._write_body_callback)
        self.c.setopt(pycurl.HEADERFUNCTION, self._write_header_callback)

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
        self.c.setopt(pycurl.SSL_VERIFYHOST, 2)
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

        self.clear_headers()

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
            aiachaser_on = b"on (using aia-chaser)"
            if options["ssl_verify"] in [True, b"on", aiachaser_on]:
                if options["ssl_verify"] == aiachaser_on:
                    self.ssl_aiachaser = True
                else:
                    self.ssl_aiachaser = False
                    self.c.setopt(pycurl.CAINFO, certifi.where())
                ssl_verify = 1
            else:
                ssl_verify = 0

            self.c.setopt(pycurl.SSL_VERIFYPEER, ssl_verify)
            self.c.setopt(pycurl.SSL_VERIFYHOST, ssl_verify * 2)

    def add_cookies(self):
        """
        put cookies from curl handle to cj.
        """
        if self.cj:
            self.cj.set_cookies(self.c.getinfo(pycurl.INFO_COOKIELIST))

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
        self._body_buffer = io.BytesIO()

        self.exception = None

        self.decode = decode

        url = myquote(url)

        if get:
            get = urlencode(get)
            url = f"{url}?{get}"

        if self.ssl_aiachaser and url.startswith("https://"):
            chaser = AiaChaser()
            try:
                pem_data = "".join([
                    cert.public_bytes(encoding=Encoding.PEM).decode("ascii")
                    for cert in chaser.fetch_ca_chain_for_url(url)
                ])
            except Exception as exc:
                self.log.warning(f"AiaChaser failed with {exc}")
                aia_cainfo = certifi.where()

            else:
                with tempfile.NamedTemporaryFile(mode="wt",prefix="aia_", suffix=".pem", delete=False) as tmp:
                    tmp.write(pem_data)
                    if self.aia_cainfo:
                        os.remove(self.aia_cainfo)
                    aia_cainfo = self.aia_cainfo = tmp.name

            self.c.setopt(pycurl.CAINFO, aia_cainfo)

        self.c.setopt(pycurl.URL, url)

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

        if isinstance(referer, str):
            self.last_url = referer

        if referer and self.last_url:
            self.c.setopt(pycurl.REFERER, to_bytes(self.last_url))

        if cookies:
            self.c.setopt(pycurl.COOKIEFILE, b"")
            self.c.setopt(pycurl.COOKIEJAR, b"")
            if isinstance(cookies, list) and self.cj:
                self.cj.set_cookies(cookies)
            self.get_cookies()

    def load(
        self,
        url,
        get=None,
        post=None,
        referer=True,
        cookies=True,
        just_header=False,
        multipart=False,
        decode=True,
        redirect=True,
        save_cookies=True,
    ):
        """
        load and returns a given page.
        """
        self.set_request_context(url, get, post, referer, cookies, multipart, decode)

        self._header_buffer = b""
        self.response_headers.clear(use_defaults=False)

        self.c.setopt(pycurl.HTTPHEADER, self.request_headers.to_pycurl())

        if not redirect:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)

        elif type(redirect) is int:
            self.c.setopt(pycurl.MAXREDIRS, redirect)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 1)

        try:
            self.c.perform()
        except pycurl.error as exc:
            if exc.args[0] == pycurl.E_WRITE_ERROR and self.exception:
                raise self.exception from None
            else:
                raise
        finally:
            if self.aia_cainfo:
                os.remove(self.aia_cainfo)
                self.aia_cainfo = None

        if not self.response_headers:
            self.response_headers.parse(self._header_buffer)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 0)

        if not redirect:
            self.c.setopt(pycurl.FOLLOWLOCATION, 1)

        elif type(redirect) is int:
            self.c.setopt(pycurl.MAXREDIRS, self.default_max_redirect)

        self.c.setopt(pycurl.POSTFIELDS, b"")
        self.last_effective_url = self.c.getinfo(pycurl.EFFECTIVE_URL)

        if save_cookies:
            self.add_cookies()

        self.code = self.verify_header()

        res = self._header_buffer if just_header else self.get_response()

        if decode:
            res = self.response_headers if just_header else self.decode_response(res)

        self._body_buffer.close()
        self._body_buffer = None

        return res

    def upload(
        self,
        filename,
        url,
        get=None,
        referer=True,
        cookies=True,
        just_header=False,
        decode=True,
        redirect=True,
        save_cookies=True,
    ):
        """
        Uploads a file at url and returns response content.

        :param filename: path of the file to upload
        :param url: URL to upload to
        :param get: Query string parameters
        :param referer: Either a str with referrer, True to use default, False to disable
        :param cookies: True or False or list of tuples [(domain, name, value)]
        :param just_header: If True only the header will be retrieved and returned as dict
        :param redirect: Either a number with maximum redirections, True to use default or False to disable
        :param decode: The codec name to decode the output, True to use codec from http header, should be True in most cases
        :param save_cookies: Weather to save received cookies
        :return: Response content
        """
        with open(os.fsencode(filename), mode="rb") as fp:
            self.set_request_context(url, get, None, referer, cookies, False)

            self._header_buffer = b""

            self.c.setopt(pycurl.HTTPHEADER, self.request_headers.to_pycurl())

            if not redirect:
                self.c.setopt(pycurl.FOLLOWLOCATION, 0)

            elif isinstance(redirect, int):
                self.c.setopt(pycurl.MAXREDIRS, redirect)

            self.c.setopt(pycurl.UPLOAD, 1)
            self.c.setopt(pycurl.READFUNCTION, fp.read)
            self.c.setopt(pycurl.INFILESIZE, os.fstat(fp.fileno()).st_size)

            if just_header:
                self.c.setopt(pycurl.NOBODY, 1)

            self.c.perform()

            if just_header:
                self.c.setopt(pycurl.NOBODY, 0)

            if not redirect:
                self.c.setopt(pycurl.FOLLOWLOCATION, 1)

            elif type(redirect) is int:
                self.c.setopt(pycurl.MAXREDIRS, self.default_max_redirect)

            self.c.setopt(pycurl.UPLOAD, 0)
            self.c.setopt(pycurl.INFILESIZE, 0)

            self.c.setopt(pycurl.POSTFIELDS, "")
            self.last_effective_url = self.c.getinfo(pycurl.EFFECTIVE_URL)

            if save_cookies:
                self.add_cookies()

            self.code = self.verify_header()

            res = self._header_buffer if just_header else self.get_response()

            if decode:
                res = (
                    to_str(res, encoding="iso-8859-1")
                    if just_header
                    else self.decode_response(res)
                )

            self._body_buffer.close()
            self._body_buffer = None

            return res

    def verify_header(self):
        """
        raise an exceptions on bad headers.
        """
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in BAD_STATUS_CODES:
            response = self.decode_response(self.get_response()) if self.decode else self.get_response()
            self._body_buffer.close()
            self._body_buffer = None

            # 404 will NOT raise an exception
            raise BadHeader(code, self.response_headers, response)

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
        if self._body_buffer is None:
            return b""
        else:
            return self._body_buffer.getvalue()

    def decode_response(self, response):
        """
        decode with correct encoding, relies on header.
        """
        encoding = "utf-8"  #: default encoding

        if isinstance(self.decode, str):
            encoding = self.decode

        elif self.decode:
            #: detect encoding
            for content_value in self.response_headers.get_list("Content-Type"):
                content_type, content_params = parse_header_line(content_value)
                if content_type.startswith("text/") or content_type.startswith("application/") and "charset" in content_params:
                    encoding = content_params["charset"]
                    break

        try:
            # self.log.debug(f"Decoded {encoding}")
            if codecs.lookup(encoding).name == "utf-8" and response.startswith(
                codecs.BOM_UTF8
            ):
                encoding = "utf-8-sig"

            decoder = codecs.getincrementaldecoder(encoding)("replace")
            response = decoder.decode(response, True)

        except LookupError:
            self.log.debug(f"No Decoder found for {encoding}")

        except UnicodeDecodeError:
            self.log.debug(f"Error when decoding string from {encoding}", exc_info=True)

        response = html_unescape(response)

        return response

    def _write_body_callback(self, buf):
        """
        writes response.
        """
        if self.abort:
            self.exception = Abort()
            return pycurl.E_WRITE_ERROR

        elif self.limit and self._body_buffer.tell() > self.limit:
            rep = self.get_response()
            with open("response.dump", mode="wb") as fp:
                fp.write(rep)

            self.exception = Exception(f"Loaded URL exceeded limit ({self.limit})")
            return pycurl.E_WRITE_ERROR

        self._body_buffer.write(buf)

        return None  #: Everything is OK, please continue

    def _write_header_callback(self, buf):
        """
        writes header.
        """
        self._header_buffer += buf

        if self._header_buffer.endswith(b"\r\n\r\n"):
            self.response_headers.parse(self._header_buffer)

    def add_header(self, name, value):
        """Append a value to a header name without replacing existing ones."""
        self.request_headers.add(name, value)

    def set_header(self, name, value):
        """Set a header to a single value, replacing all existing values for the name."""
        self.request_headers.set(name, value)

    def remove_header(self, name, value=None):
        self.request_headers.remove(name, value)

    def clear_headers(self, use_defaults=True):
        self.request_headers.clear(use_defaults=use_defaults)


    def close(self):
        """
        cleanup, unusable after this.
        """
        if self._body_buffer:
            self._body_buffer.close()
            del self._body_buffer

        if hasattr(self, "cj"):
            del self.cj

        if hasattr(self, "c"):
            self.c.close()
            del self.c
