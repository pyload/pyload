# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

import os

from colorclass import *
from future import standard_library

standard_library.install_aliases()


for tag, reset, _, _ in list_tags():
    if not tag:
        continue
    globals()[tag] = lambda msg: Color(
        "{{{0}}}{1}{{{2}}}".format(tag, msg, reset))

if os.name == 'nt':
    Windows.enable(auto_colors=True, reset_atexit=True)
elif is_light():
    set_light_background()
else:
    set_dark_background()

# Cleanup
del os
