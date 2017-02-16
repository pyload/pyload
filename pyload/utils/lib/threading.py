# -*- coding: utf-8 -*-
#
# Threading emulation for platform without the `threading` module

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

standard_library.install_aliases()
try:
    from threading import *
except ImportError:
    from dummy_threading import *
