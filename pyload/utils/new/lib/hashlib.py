# -*- coding: utf-8 -*-
#
# Hashlib legacy patch

from __future__ import absolute_import
from __future__ import unicode_literals

from hashlib import *

if 'algorithms' not in globals():
    algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
