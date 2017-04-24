# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

from __future__ import absolute_import

import builtins

builtins._ = lambda x: x  # NOTE: gettext pre-start fixup

from .parser import ConfigParser
from .parser import ConfigSection

# Cleanup
del builtins
