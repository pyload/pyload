# -*- coding: utf-8 -*-

import os
import re
import time
import urllib.request

from pyload.core.utils.convert import to_str
from pyload.core.utils.old import safename

from ..base.container import BaseContainer


class TORRENT(BaseContainer):
    __name__ = "TORRENT"
    __type__ = "container"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"(?:file|https?)://.+\.torrent|magnet:\?.+|(?!(?:file|https?)://).+\.(?:torrent|magnet)"
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

    CONTAINER_PATTERN = r"(?!(?:file|https?)://).+\.(?:torrent|magnet)"
    DECRYPTER_PATTERN = r"(?:file|https?)://.+\.torrent|magnet:\?.+"

    def process(self, pyfile):
        if re.match(self.DECRYPTER_PATTERN, pyfile.url) is not None:
            self.log_error(self._("No plugin is associated with torrents / magnets"),
                           self._("Please go to plugin settings -> TORRENT and select your preferred plugin"))

            self.fail(self._("No plugin is associated with torrents / magnets"))

        elif re.match(self.CONTAINER_PATTERN, pyfile.url) is not None:
            return super().process(pyfile)

    def decrypt(self, pyfile):
        fs_filename = os.fsencode(pyfile.url)
        with open(fs_filename, mode="rb") as fp:
            torrent_content = fp.read()

        time_ref = "{:.2f}".format(time.time())[-6:].replace(".", "")
        pack_name = "torrent {}".format(time_ref)

        if pyfile.url.endswith(".magnet"):
            if torrent_content.startswith(b"magnet:?"):
                self.packages.append((pyfile.package().name, [to_str(torrent_content)], pyfile.package().folder))

        elif pyfile.url.endswith(".torrent"):
            m = re.search(rb"name(\d+):", torrent_content)
            if m:
                m = re.search(
                    b"".join((b"name", m.group(1), b":(.{", m.group(1), b"})")),
                    torrent_content
                )
                if m:
                    pack_name = safename(to_str(m.group(1)))

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
