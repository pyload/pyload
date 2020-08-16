# -*- coding: utf-8 -*-

import os
import re
import time
import urllib.request

from pyload.core.utils.old import safename

from ..base.container import BaseContainer


class TORRENT(BaseContainer):
    __name__ = "TORRENT"
    __type__ = "container"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"^(?!file://).+\.torrent$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """TORRENT container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        with open(pyfile.url, mode="rb") as fp:
            torrent_content = fp.read()

        time_ref = "{:.2f}".format(time.time())[-6:].replace(".", "")

        pack_name = "torrent {}".format(time_ref)
        m = re.search(r"name(\d+):", torrent_content)
        if m:
            m = re.search(
                r"name{}:(.{{{}}})".format(m.group(1), m.group(1)), torrent_content
            )
            if m:
                pack_name = safename(m.group(1))

        torrent_filename = os.path.join(
            self.pyload.tempdir, "tmp_{}.torrent".format(pack_name)
        )
        with open(torrent_filename, mode="wb") as fp:
            fp.write(torrent_content)

        self.packages.append(
            (
                pack_name,
                ["file://{}".format(urllib.request.pathname2url(torrent_filename))],
                pack_name,
            )
        )
