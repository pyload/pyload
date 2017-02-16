# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from pyload.plugin.network.curldownload import CurlDownload
from pyload.plugin.network.curlrequest import CurlRequest

__version__ = "0.1"

DefaultRequest = CurlRequest
DefaultDownload = CurlDownload
