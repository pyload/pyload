# -*- coding: utf-8 -*-

import codecs

from ..internal.Container import Container
from ..internal.misc import encode


class TXT(Container):
    __name__ = "TXT"
    __type__ = "container"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r'.+\.(txt|text)$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("flush", "bool", "Flush list after adding", False),
                  ("encoding", "str", "File encoding", "utf-8")]

    __description__ = """Read link lists in plain text formats"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org"),
                   ("jeix", "jeix@hasnomail.com")]

    def decrypt(self, pyfile):
        try:
            encoding = codecs.lookup(self.config.get('encoding')).name

        except Exception:
            encoding = "utf-8"

        fs_filename = encode(pyfile.url)
        txt = codecs.open(fs_filename, 'r', encoding)
        curPack = "Parsed links from %s" % pyfile.name
        packages = {curPack: [], }

        for link in txt.readlines():
            link = link.strip()

            if not link:
                continue

            if link.startswith(";"):
                continue

            if link.startswith("[") and link.endswith("]"):
                #: New package
                curPack = link[1:-1]
                packages[curPack] = []
                continue

            packages[curPack].append(link)

        txt.close()

        #: Empty packages fix
        for key, value in packages.items():
            if not value:
                packages.pop(key, None)

        if self.config.get('flush'):
            try:
                txt = open(fs_filename, 'wb')
                txt.close()

            except IOError:
                self.log_warning(_("Failed to flush list"))

        for name, links in packages.items():
            self.packages.append((name, links, name))
