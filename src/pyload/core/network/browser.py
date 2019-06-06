# -*- coding: utf-8 -*-

from logging import getLogger

from pyload import APPID

from .http.http_download import HTTPDownload
from .http.http_request import HTTPRequest


class Browser:
    def __init__(self, bucket=None, options={}):
        self.log = getLogger(APPID)

        self.options = options  #: holds pycurl options
        self.bucket = bucket

        self.cj = None  #: needs to be setted later
        self.http = None
        self._size = 0

        self.renew_http_request()
        self.dl = None

    def renew_http_request(self):
        try:
            self.http.close()
        except Exception:
            pass
        self.http = HTTPRequest(self.cj, self.options)

    def set_last_url(self, val):
        self.http.last_url = val

    # tunnel some attributes from HTTP Request to Browser
    last_effective_url = property(lambda self: self.http.last_effective_url)
    last_url = property(lambda self: self.http.last_url, set_last_url)
    code = property(lambda self: self.http.code)
    cookie_jar = property(lambda self: self.cj)

    def set_cookie_jar(self, cj):
        self.cj = cj
        self.http.cj = cj

    @property
    def speed(self):
        if self.dl:
            return self.dl.speed
        return 0

    @property
    def size(self):
        if self._size:
            return self._size
        if self.dl:
            return self.dl.size
        return 0

    @property
    def arrived(self):
        if self.dl:
            return self.dl.arrived
        return 0

    @property
    def percent(self):
        if not self.size:
            return 0
        return (self.arrived * 100) // self.size

    def clear_cookies(self):
        if self.cj:
            self.cj.clear()
        self.http.clear_cookies()

    def clear_referer(self):
        self.http.last_url = None

    def abort_downloads(self):
        self.http.abort = True
        if self.dl:
            self._size = self.dl.size
            self.dl.abort = True

    def http_download(
        self,
        url,
        filename,
        get={},
        post={},
        ref=True,
        cookies=True,
        chunks=1,
        resume=False,
        progress_notify=None,
        disposition=False,
    ):
        """
        this can also download ftp.
        """
        self._size = 0
        self.dl = HTTPDownload(
            url,
            filename,
            get,
            post,
            self.last_effective_url if ref else None,
            self.cj if cookies else None,
            self.bucket,
            self.options,
            progress_notify,
            disposition,
        )
        name = self.dl.download(chunks, resume)
        self._size = self.dl.size

        self.dl = None

        return name

    def load(self, *args, **kwargs):
        """
        retrieves page.
        """
        return self.http.load(*args, **kwargs)

    def put_header(self, name, value):
        """
        add a header to the request.
        """
        self.http.put_header(name, value)

    def add_auth(self, pwd):
        """
        Adds user and pw for http auth.

        :param pwd: string, user:password
        """
        self.options["auth"] = pwd
        self.renew_http_request()  #: we need a new request

    def remove_auth(self):
        if "auth" in self.options:
            del self.options["auth"]
        self.renew_http_request()

    def set_option(self, name, value):
        """
        Adds an option to the request, see HTTPRequest for existing ones.
        """
        self.options[name] = value

    def delete_option(self, name):
        if name in self.options:
            del self.options[name]

    def clear_headers(self):
        self.http.clear_headers()

    def close(self):
        """
        cleanup.
        """
        if hasattr(self, "http"):
            self.http.close()
            del self.http
        if hasattr(self, "dl"):
            del self.dl
        if hasattr(self, "cj"):
            del self.cj
