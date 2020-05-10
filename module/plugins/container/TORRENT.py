# -*- coding: utf-8 -*-

import re
import time
import urllib

from ..internal.Container import Container
from ..internal.misc import decode, fs_encode, fsjoin, safename


class TORRENT(Container):
    __name__ = "TORRENT"
    __type__ = "container"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r'(?:file|https?)://.+\.torrent|magnet:\?.+|(?!file://).+\.(torrent|magnet)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """TORRENT container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CONTAINER_PATTERN = r'(?!file://).+\.(torrent|magnet)'
    CRYPTER_PATTERN = r'(?:file|https?)://.+\.torrent|magnet:\?.+'

    def process(self, pyfile):
        if re.match(self.CRYPTER_PATTERN, pyfile.url) is not None:
            self.log_error(_("No plugin is associated with torrents / magnets"),
                           _("Please go to plugin settings -> TORRENT and select your preferred plugin"))

            self.fail(_("No plugin is associated with torrents / magnets"))

        elif re.match(self.CONTAINER_PATTERN, pyfile.url) is not None:
            return Container.process(self, pyfile)

    def decrypt(self, pyfile):
        fs_filename = fs_encode(pyfile.url)
        with open(fs_filename, "rb") as f:
            torrent_content = f.read()

        time_ref = ("%.2f" % time.time())[-6:].replace(".", "")
        pack_name = "torrent_%s" % time_ref

        if pyfile.url.endswith(".magnet"):
            if torrent_content.startswith("magnet:?"):
                self.packages.append((pyfile.package().name, [torrent_content], pyfile.package().folder))

        elif pyfile.url.endswith(".torrent"):
            m = re.search(r'name(\d+):', torrent_content)
            if m:
                m = re.search(r'name%s:(.{%s})' % (m.group(1), m.group(1)), torrent_content)
                if m:
                    pack_name = safename(decode(m.group(1)))

            torrent_filename = fsjoin("tmp", "tmp_%s.torrent" % pack_name)
            with open(torrent_filename, "wb") as f:
                f.write(torrent_content)

            self.packages.append((pack_name, ["file://%s" % urllib.pathname2url(torrent_filename.encode('utf8'))], pack_name))
