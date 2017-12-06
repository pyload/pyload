# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import io
from codecs import BOM_UTF8, getincrementaldecoder, lookup
from urllib.parse import quote, urlencode

from future import standard_library
from future.builtins import dict, int

import pycurl
from pyload.requests.base.load import LoadRequest
from pyload.requests.base.request import (BAD_HTTP_RESPONSES, Abort,
                                          ResponseException)
from pyload.requests.cookie import CookieJar
from pyload.utils.check import isiterable
from pyload.utils.convert import to_bytes, to_str

standard_library.install_aliases()


pycurl.global_init(pycurl.GLOBAL_DEFAULT)


def safequote(url):
    return quote(to_bytes(url), safe="%/:=&?~#+!$,;'@()*[]")


def safeurlencode(data):
    if isiterable(data):
        res = urlencode(
            dict((to_bytes(x), to_bytes(y)) for x, y in dict(data).items()))
    else:
        res = urlencode(to_bytes(data))
    return res


class CurlRequest(LoadRequest):
    """Request class based on libcurl."""
    CONTEXT_CLASS = CookieJar
    DEFAULT_LIMIT = 1 << 20

    def __init__(self, *args, **kwargs):
        self.curl = pycurl.Curl()
        self.limit = kwargs.pop(
            'limit', self.DEFAULT_LIMIT)  # TODO: Rename `limit`

        super(CurlRequest, self).__init__(*args, **kwargs)

        self.rep = None
        self.last_url = None
        self.last_effective_url = None
        self.header = ''

        # cookiejar defines the context
        self.cj = self.context

        self.setopt(pycurl.WRITEFUNCTION, self.write)
        self.setopt(pycurl.HEADERFUNCTION, self.write_header)

    # TODO: addHeader

    @property
    def http(self):
        self.log.debug('Deprecated usage of req.http, just use req instead')
        return self

    def init_context(self):
        self.init_handle()

        if self.config:
            self.set_interface(self.config)
            self.init_options(self.config)

    def setopt(self, option, value):
        self.curl.setopt(option, value)

    def unsetopt(self, option):
        self.curl.unsetopt(option)

    def init_handle(self):
        """Sets common options to curl handle."""
        self.setopt(pycurl.FOLLOWLOCATION, 1)
        self.setopt(pycurl.MAXREDIRS, 5)
        self.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.setopt(pycurl.NOSIGNAL, 1)
        self.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, 'AUTOREFERER'):
            self.setopt(pycurl.AUTOREFERER, 1)
        self.setopt(pycurl.SSL_VERIFYPEER, 0)
        # Interval for low speed, detects connection loss, but can abort dl if
        # hoster stalls the download
        self.setopt(pycurl.LOW_SPEED_TIME, 45)
        self.setopt(pycurl.LOW_SPEED_LIMIT, 5)

        # do not save the cookies
        self.setopt(pycurl.COOKIEFILE, '')
        self.setopt(pycurl.COOKIEJAR, '')

        # self.setopt(pycurl.VERBOSE, 1)

        self.setopt(
            pycurl.USERAGENT,
            'Mozilla/5.0 (Windows NT 10.0; Win64; rv:53.0) '
            'Gecko/20100101 Firefox/53.0')
        if pycurl.version_info()[7]:
            self.setopt(pycurl.ENCODING, 'gzip,deflate')

        self.headers.update(
            {'Accept': '*/*',
             'Accept-Language': 'en-US,en',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
             'Connection': 'keep-alive',
             'Keep-Alive': '300',
             'Expect': ''})

    def set_interface(self, options):
        interface, proxy, ipv6 = options[
            'interface'], options['proxies'], options['ipv6']

        if interface and interface.lower() != 'none':
            self.setopt(pycurl.INTERFACE, interface)

        if proxy:
            if proxy['type'] == 'socks4':
                self.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
            elif proxy['type'] == 'socks5':
                self.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            else:
                self.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            self.setopt(pycurl.PROXY, proxy['host'][0])
            self.setopt(pycurl.PROXYPORT, proxy['host'][1])

            if proxy['username']:
                userpwd = '{0}:{1}'.format(
                    proxy['username'], proxy['password'])
                self.setopt(pycurl.PROXYUSERPWD, userpwd)

        if ipv6:
            self.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
        else:
            self.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        if 'timeout' in options:
            self.setopt(pycurl.LOW_SPEED_TIME, options['timeout'])

        if 'auth' in options:
            self.setopt(pycurl.USERPWD, self.options['auth'])

    def init_options(self, options):
        """Sets same options as available in pycurl."""
        for k, v in options.items():
            if not hasattr(pycurl, k):
                continue
            self.setopt(getattr(pycurl, k), v)

    def set_request_context(self, url, get, post,
                            referer, cookies, multipart=False):
        """Sets everything needed for the request."""
        self.rep = io.BytesIO()
        url = safequote(url)

        if get:
            get = urlencode(get)
            url = '{0}?{1}'.format(url, get)

        self.setopt(pycurl.URL, url)

        if post:
            self.setopt(pycurl.POST, 1)
            if not multipart:
                post = safeurlencode(post)
                self.setopt(pycurl.POSTFIELDS, post)
            else:
                post = [(x, to_bytes(y))
                        for x, y in post.items()]
                self.setopt(pycurl.HTTPPOST, post)
        else:
            self.setopt(pycurl.POST, 0)

        if referer and self.last_url:
            self.headers['Referer'] = self.last_url
        else:
            self.headers['Referer'] = ''

        if cookies:
            for c in self.cj.output().splitlines():
                self.setopt(pycurl.COOKIELIST, c)
        else:
            # Magic string that erases all cookies
            self.setopt(pycurl.COOKIELIST, 'ALL')

        # TODO: remove auth again
        if 'auth' in self.options:
            self.setopt(pycurl.USERPWD, self.options['auth'])

        self.setopt(pycurl.HTTPHEADER, self.headers.list())

    def load(self, url, get=None, post=None, referer=True, cookies=True,
             just_header=False, multipart=False, decode=False):
        """Load and returns a given page."""
        self.set_request_context(url, get, post, referer, cookies, multipart)

        # TODO: use http/rfc message instead
        self.header = ''

        if 'header' in self.options:
            # TODO
            # print("custom header not implemented")
            self.setopt(pycurl.HTTPHEADER, self.options['header'])

        if just_header:
            self.setopt(pycurl.FOLLOWLOCATION, 0)
            self.setopt(pycurl.NOBODY, 1)  # TODO: nobody= no post?

            # overwrite HEAD request, we want a common request type
            if post:
                self.setopt(pycurl.CUSTOMREQUEST, 'POST')
            else:
                self.setopt(pycurl.CUSTOMREQUEST, 'GET')

            try:
                self.curl.perform()
                rep = self.header
            finally:
                self.setopt(pycurl.FOLLOWLOCATION, 1)
                self.setopt(pycurl.NOBODY, 0)
                self.unsetopt(pycurl.CUSTOMREQUEST)

        else:
            self.curl.perform()
            rep = self.get_response()

        self.setopt(pycurl.POSTFIELDS, '')
        self.last_url = safequote(url)
        self.last_effective_url = self.curl.getinfo(pycurl.EFFECTIVE_URL)
        if self.last_effective_url:
            self.last_url = self.last_effective_url

        try:
            self.code = self.verify_header()
        finally:
            self.rep.close()
            self.rep = None

        if cookies:
            self.parse_cookies()

        if decode:
            rep = self.decode_response(rep)

        return rep

    def parse_cookies(self):
        for c in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            # http://xiix.wordpress.com/2006/03/23/mozillafirefox-cookie-format
            domain, _, path, secure, expires, name, value = c.split('\t')
            # http only was added in py 2.6
            domain = domain.replace('#HttpOnly_', '')
            self.cj.set(domain, name, value, path, expires, secure)

    def verify_header(self):
        """Raise an exceptions on bad headers."""
        code = int(self.curl.getinfo(pycurl.RESPONSE_CODE))
        if code in BAD_HTTP_RESPONSES:
            raise ResponseException(
                code,
                self.get_response(),
                self.header)
        return code

    def get_response(self):
        """Retrieve response from string io."""
        if self.rep is None:
            return ''
        else:
            return self.rep.getvalue()

    def decode_response(self, rep):
        """Decode with correct encoding, relies on header."""
        header = self.header.splitlines()
        encoding = 'utf8'  # default encoding

        for line in header:
            line = line.lower().replace(' ', '')
            if (not line.startswith('content-type:') or
                    ('text' not in line and 'application' not in line)):
                continue

            _, delemiter, charset = line.rpartition('charset=')
            if delemiter:
                charset = charset.split(';')
                if charset:
                    encoding = charset[0]

        try:
            # self.log.debug("Decoded {0}".format(encoding))
            if lookup(encoding).name == 'utf-8' and rep.startswith(BOM_UTF8):
                encoding = 'utf-8-sig'

            decoder = getincrementaldecoder(encoding)('replace')
            rep = decoder.decode(rep, True)

            # TODO: html_unescape as default

        except LookupError:
            self.log.debug('No Decoder found for {0}'.format(encoding))
        except Exception:
            self.log.debug(
                'Error when decoding string from {0}'.format(encoding))

        return rep

    def write(self, buf):
        """Writes response."""
        if self.rep.tell() > self.limit or self._abort:
            rep = self.get_response()
            self.close()
            if self._abort:
                raise Abort
            with io.open('response.dump', mode='wb') as fp:
                fp.write(rep)
            raise Exception('Loaded Url exceeded limit')

        self.rep.write(buf)

    def write_header(self, buf):
        """Writes header."""
        self.header += to_str(buf)

    def reset(self):
        self.cj.clear()
        self.options.clear()

    def close(self):
        """Cleanup, unusable after this."""
        if self.rep is not None:
            self.rep.close()
            del self.rep
        if hasattr(self, 'cj'):
            del self.cj
        if hasattr(self, 'c'):
            self.curl.close()
