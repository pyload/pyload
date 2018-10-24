# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import builtins

import _locale
import logging
import locale
import os
import pkg_resources
import semver
import sys
import tempfile
import traceback


### Info ###

try:
    dist_name = __name__
    pkgdir = pkg_resources.resource_filename(dist_name, "")
    __version__ = pkg_resources.get_distribution(dist_name).version

except pkg_resources.DistributionNotFound:
    pkgdir = os.path.realpath(os.path.join(__file__, ".."))
    ver_path = os.path.join(pkgdir, "..", "..", "VERSION.md")
    with open(ver_path) as f:
        __version__ = f.read().strip()

finally:
    __version_info__ = semver.parse_version_info(__version__)
    del pkg_resources
    del semver

# remove from builtins and keep them just here?
builtins.PKGDIR = pkgdir
builtins.HOMEDIR = os.path.expanduser("~")
builtins.DATADIR = os.getenv("APPDATA") if os.name == "nt" else builtins.HOMEDIR
builtins.TMPDIR = tempfile.gettempdir()

# TODO: remove
builtins._ = lambda x: x
builtins.REQUESTS = None
builtins.ADDONMANAGER = None


### Locale ###

locale.setlocale(locale.LC_ALL, "")
if os.name == "nt":
    _locale._getdefaultlocale = lambda *args: ["en_US", "utf_8_sig"]


### Exception logger ###

exc_logger = logging.getLogger("exception")

def excepthook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    msg_list = traceback.format_exception_only(exc_type, exc_value)
    exc_info = (exc_type, exc_value, exc_traceback)
    exc_logger.exception(msg_list[-1], exc_info=exc_info)

sys.excepthook = excepthook
del excepthook


### Cleanup ###

del _locale
del pkgdir
del locale
del logging
del os
del sys
del tempfile
