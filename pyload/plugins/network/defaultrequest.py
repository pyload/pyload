# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

from future import standard_library

from .curldownload import CurlDownload
from .curlrequest import CurlRequest

standard_library.install_aliases()

__version__ = "0.1"

DefaultRequest = CurlRequest
DefaultDownload = CurlDownload
