#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import importlib.metadata
import importlib.resources
import packaging.version
import locale
import logging
import os
import sys
import traceback

import _locale
import semver

# Info
APPID = "pyload"
PKGNAME = "pyload-ng"
PKGDIR = str(importlib.resources.files(__name__))

USERHOMEDIR = os.path.expanduser("~")
os.chdir(USERHOMEDIR)

try:
    __version__ = packaging.version.Version(importlib.metadata.version(PKGNAME)).base_version
except importlib.metadata.PackageNotFoundError:
    __version__ =  "0.5.0"
__version_info__ = semver.parse_version_info(__version__)

# Application wide global storage
class __storage:
    def get(self, name, default=None):
        return self.__dict__.get(name, default)
    def items(self):
        return self.__dict__.items()
    def keys(self):
        return self.__dict__.keys()
    def values(self):
        return self.__dict__.values()
    def clear(self):
        self.__dict__.clear()
    def __contains__(self, name):
        return name in self.__dict__
g = __storage()

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
