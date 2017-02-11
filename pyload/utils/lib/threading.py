# -*- coding: utf-8 -*-
#
# Threading emulation for platform without the `threading` module

try:
    from threading import *
except ImportError:
    from dummy_threading import *
