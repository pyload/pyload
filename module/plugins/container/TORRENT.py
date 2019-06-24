# -*- coding: utf-8 -*-

import os
import re
import time
import urllib

from ..internal.Container import Container
from ..internal.misc import encode, safename


class TORRENT(Container):
    __name__ = "TORRENT"
    __type__ = "container"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'^(?!file://).+\.torrent$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """TORRENT container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        fs_filename = encode(pyfile.url)
        with open(fs_filename, "rb") as f:
            torrent_content = f.read()

        time_ref = ("%.2f" % time.time())[-6:].replace(".", "")

        pack_name = "torrent %s" % time_ref
        m = re.search(r'name(\d+):', torrent_content)
        if m:
            m = re.search(r'name%s:(.{%s})' % (m.group(1), m.group(1)), torrent_content)
            if m:
                pack_name = safename(m.group(1))

        torrent_filename = os.path.join("tmp", "tmp_%s.torrent" % pack_name)
        with open(torrent_filename, "wb") as f:
            f.write(torrent_content)

        self.packages.append((pack_name, ["file://%s" % urllib.pathname2url(torrent_filename)], pack_name))
