# -*- coding: utf-8 -*-

# Test configuration
from __future__ import absolute_import, unicode_literals

from future import standard_library

standard_library.install_aliases()

credentials = ("TestUser", "pwhere")
webport = 8921
wsport = 7558

webaddress = "http://localhost:{0:d}/api".format(webport)
wsaddress = "ws://localhost:{0:d}/api".format(wsport)
