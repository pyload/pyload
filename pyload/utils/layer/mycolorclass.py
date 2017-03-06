# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import unicode_literals

import os

from colorclass import *

for tag, reset, _, _ in list_tags():
    if not tag:
        continue
    globals()[tag] = lambda msg: Color(
        '{{{}}}{}{{{}}}'.format(tag, msg, reset))

if os.name == 'nt':
    Windows.enable(auto_colors=True, reset_atexit=True)
elif is_light():
    set_light_background()
else:
    set_dark_background()

# Cleanup
del os
