# -*- coding: utf-8 -*-
# @author: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import builtins
import os

builtins._ = lambda x: x  # NOTE: gettext pre-start fixup
builtins.PACKDIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..'))
builtins.COREDIR = os.path.join(PACKDIR, 'pyload', 'core')

from .assistant import SetupAssistant

# Cleanup
del builtins, os
