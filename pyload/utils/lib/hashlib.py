# -*- coding: utf-8 -*-
#
# Hashlib legacy patch

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from hashlib import *

from future import standard_library

standard_library.install_aliases()

if 'algorithms' not in globals():
    algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
