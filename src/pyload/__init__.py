# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

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

__version__ = pkg_resources.get_distribution(PKGNAME).parsed_version.base_version
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
