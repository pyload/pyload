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

from __future__ import absolute_import, division, unicode_literals

from future import standard_library
standard_library.install_aliases()
import builtins
import codecs
import os
import sys
import tempfile

builtins.PACKDIR = PACKDIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..'))
builtins.COREDIR = COREDIR = os.path.join(PACKDIR, 'pyload', 'core')
builtins.USERDIR = USERDIR = os.path.expanduser('~')
builtins.DATADIR = DATADIR = os.getenv(
    'APPDATA') if os.name == 'nt' else USERDIR
builtins.TMPDIR = TMPDIR = tempfile.gettempdir()

sys.path.append(PACKDIR)
sys.path.append(os.path.join(PACKDIR, 'lib'))

builtins.REQUEST = None  # TODO: Remove
builtins.ADDONMANAGER = None  # TODO: Remove
builtins._ = lambda x: x  # NOTE: gettext pre-start fixup

# codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
# sys.stdout = codecs.getwriter(sys.console_encoding(sys.stdout.encoding))(sys.stdout, errors="replace")

from . import api
from . import database
from . import datatype
from . import manager
from . import network
from . import thread
from .init import (Core, Restart, Shutdown, info, quit, restart, setup, start,
                   status, upgrade, version)

# Cleanup
del builtins, codecs, os, sys, tempfile
