# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import _locale
import logging
import locale
import os
import pkg_resources
import semver
import sys
import traceback


# Info

APPID = "pyload"

PKGNAME = "pyload-ng"
PKGDIR = pkg_resources.resource_filename(__name__, "")

USERHOMEDIR = os.path.expanduser("~")
os.chdir(USERHOMEDIR)

try:
    __version__ = pkg_resources.get_distribution(PKGNAME).parsed_version.base_version
except pkg_resources.DistributionNotFound:
    __version__ =  "0.5.0"
__version_info__ = semver.parse_version_info(__version__)


# Locale

locale.setlocale(locale.LC_ALL, "")
if os.name == "nt":
    _locale._getdefaultlocale = lambda *args: ["en_US", "utf_8_sig"]


# Exception logger

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


# Cleanup

del _locale
del locale
del logging
del os
del pkg_resources
del semver
del sys
