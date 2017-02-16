# -*- coding: utf-8 -*-

# Test configuration
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
credentials = ("TestUser", "pwhere")
webport = 8921
wsport = 7558

webaddress = "http://localhost:{:d}/api".format(webport)
wsaddress = "ws://localhost:{:d}/api".format(wsport)
