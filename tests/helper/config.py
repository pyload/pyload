# -*- coding: utf-8 -*-

# Test configuration
from __future__ import unicode_literals
credentials = ("TestUser", "pwhere")
webport = 8921
wsport = 7558

webaddress = "http://localhost:{:d}/api".format(webport)
wsaddress = "ws://localhost:{:d}/api".format(wsport)
