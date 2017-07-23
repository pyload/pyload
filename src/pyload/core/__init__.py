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

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()
import builtins
import locale
import os
import tempfile

builtins.USERDIR = os.path.expanduser('~')
builtins.DATADIR = os.getenv(
    'APPDATA') if os.name == 'nt' else builtins.USERDIR
builtins.TMPDIR = tempfile.gettempdir()

# TODO: Remove
builtins.ADDONMANAGER = None

# from .__about__ import __package__
# from pkg_resources import resource_filename
# from pyload.utils.misc import install_translation

locale.setlocale(locale.LC_ALL, '')
# install_translation('core', resource_filename(__package__, 'locale'))

# codecs.register(lambda enc: codecs.lookup('utf-8') if enc == 'cp65001' else None)
# sys.stdout = codecs.getwriter(sys.console_encoding(sys.stdout.encoding))(sys.stdout, errors="replace")

from pyload.core import api, config, database, datatype, manager, network, thread
from pyload.core.iface import cleanup, quit, restart, start, status, version, upgrade
from pyload.core.init import Core, Restart, Shutdown
