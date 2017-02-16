# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

from pyload.plugin.network.curldownload import CurlDownload
from pyload.plugin.network.curlrequest import CurlRequest

standard_library.install_aliases()

__version__ = "0.1"

DefaultRequest = CurlRequest
DefaultDownload = CurlDownload
