# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from .curldownload import CurlDownload
from .curlrequest import CurlRequest


__version__ = "0.1"

DefaultRequest = CurlRequest
DefaultDownload = CurlDownload
