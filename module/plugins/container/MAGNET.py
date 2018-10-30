# -*- coding: utf-8 -*-

import codecs, os

from ..internal.Container import Container
from ..internal.misc import encode


class MAGNET(Container):
    __name__ = "MAGNET"
    __type__ = "container"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'^(?!file://).+\.magnet$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("encoding", "str", "File encoding", "utf-8")]

    __description__ = """Read magnet file links"""
    __license__ = "GPLv3"
    __authors__ = [("CodingMask", "NA")]

    def decrypt(self, pyfile):
        try:
            encoding = codecs.lookup(self.config.get('encoding')).name

        except Exception:
            encoding = "utf-8"

        fs_filename = encode(pyfile.url)
        txt = codecs.open(fs_filename, 'r', encoding)
        curPack = os.path.splitext(os.path.split(pyfile.name)[-1])[0]
        packages = {curPack: [], }
        link = txt.read().strip()
        packages[curPack].append(link)
        txt.close()

        #: Empty packages fix
        for key, value in packages.items():
            if not value:
                packages.pop(key, None)

        for name, links in packages.items():
            self.packages.append((name, links, name))
