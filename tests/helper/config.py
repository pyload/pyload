# -*- coding: utf-8 -*-

# Test configuration
from __future__ import unicode_literals
credentials = ("TestUser", "pwhere")
webPort = 8921
wsport = 7558

webAddress = "http://localhost:{:d}/api".format(webPort)
wsAddress = "ws://localhost:{:d}/api".format(wsport)
