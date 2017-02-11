# -*- coding: utf-8 -*-
#
# Threading emulation for platform without the `threading` module

from __future__ import unicode_literals

try:
    from threading import *
except ImportError:
    from dummy_threading import *
