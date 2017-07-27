# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

from pyload.requests.bucket import Bucket
from pyload.requests.curl.download import CurlDownload
from pyload.requests.curl.request import CurlRequest

standard_library.install_aliases()


class RequestFactory(object):

    def __init__(self, core):
        self.__pyload = core
        self.bucket = Bucket()
        self.update_bucket()

        self.__pyload.evm.listen_to("config:changed", self.update_config)

    @property
    def pyload_core(self):
        return self.__pyload

    def get_url(self, *args, **kwargs):
        """
        See HTTPRequest for argument list.
        """
        with CurlRequest(self.get_config()) as h:
            rep = h.load(*args, **kwargs)
        return rep

    def get_request(self, context=None, class_=CurlRequest):
        """
        Creates a request with new or given context.
        """
        # also accepts the context class directly
        if isinstance(context, class_.CONTEXT_CLASS):
            return class_(self.get_config(), context)
        elif context:
            return class_(*context)
        else:
            return class_(self.get_config())

    def get_download_request(self, request=None, class_=CurlDownload):
        """
        Instantiates a instance for downloading.
        """
        # TODO: load with plugin manager
        return class_(self.bucket, request)

    def get_interface(self):
        return self.pyload_core.config.get('connection', 'interface')

    def get_proxies(self):
        """
        Returns a proxy list for the request classes.
        """
        if not self.pyload_core.config.get('proxy', 'activated'):
            return {}
        else:
            _type = "http"
            setting = self.pyload_core.config.get('proxy', 'type').lower()
            if setting == "socks4":
                _type = "socks4"
            elif setting == "socks5":
                _type = "socks5"

            username = None
            if self.pyload_core.config.get(
                    'proxy', 'username') and self.pyload_core.config.get(
                    'proxy', 'username').lower() != "none":
                username = self.pyload_core.config.get('proxy', 'username')

            pw = None
            if self.pyload_core.config.get(
                    'proxy', 'password') and self.pyload_core.config.get(
                    'proxy', 'password').lower() != "none":
                pw = self.pyload_core.config.get('proxy', 'password')

            return {
                'type': _type,
                'address': self.pyload_core.config.get('proxy', 'host'),
                'port': self.pyload_core.config.get('proxy', 'port'),
                'username': username,
                'password': pw,
            }

    def update_config(self, section, option, value):
        """
        Updates the bucket when a config value changed.
        """
        if option in ("limit_speed", "max_speed"):
            self.update_bucket()

    def get_config(self):
        """
        Returns options needed for pycurl.
        """
        return {'interface': self.get_interface(),
                'proxies': self.get_proxies(),
                'ipv6': self.pyload_core.config.get('connection', 'ipv6')}

    def update_bucket(self):
        """
        Set values in the bucket according to settings.
        """
        max_speed = self.pyload_core.config.get('connection', 'max_speed')
        if max_speed > 0:
            self.bucket.set_rate(max_speed << 10)
        else:
            self.bucket.set_rate(-1)
