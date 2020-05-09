# -*- coding: utf-8 -*-

import fnmatch
import os
import time
import urllib

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.Crypter import Crypter
from ..internal.misc import exists, json, safejoin


class TORRENT(Crypter):
    __name__ = "TORRENT"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'(?:file|https?)://.+\.torrent|magnet:\?.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Associate torrents / magnets with plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    def decrypt(self, pyfile):
        self.log_error(_("No plugin is associated with torrents / magnets"),
                       _("Please go to plugin settings -> TORRENT and select your preferred plugin"))

        self.fail(_("No plugin is associated with torrents / magnets"))

