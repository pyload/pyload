# -*- coding: utf-8 -*-
#
# Threading emulation for platform without the `threading` module

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
try:
    from threading import *
except ImportError:
    from dummy_threading import *
