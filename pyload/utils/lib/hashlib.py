# -*- coding: utf-8 -*-
#
# Hashlib legacy patch

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from hashlib import *

if 'algorithms' not in globals():
    algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
