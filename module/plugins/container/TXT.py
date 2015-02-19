# -*- coding: utf-8 -*-

import codecs

from module.plugins.Container import Container
from module.utils import fs_encode


class TXT(Container):
    __name__    = "TXT"
    __type__    = "container"
    __version__ = "0.15"

    __pattern__ = r'.+\.(txt|text)$'
    __config__  = [("flush"   , "bool"  , "Flush list after adding", False  ),
                   ("encoding", "string", "File encoding"          , "utf-8")]

    __description__ = """Read link lists in plain text formats"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("jeix", "jeix@hasnomail.com")]


    def decrypt(self, pyfile):
        try:
            encoding = codecs.lookup(self.getConfig("encoding")).name

        except Exception:
            encoding = "utf-8"

        file     = fs_encode(pyfile.url.strip())
        txt      = codecs.open(file, 'r', encoding)
        curPack  = "Parsed links from %s" % pyfile.name
        packages = {curPack:[],}

        for link in txt.readlines():
            link = link.strip()

            if not link:
                continue

            if link.startswith(";"):
                continue

            if link.startswith("[") and link.endswith("]"):
                # new package
                curPack = link[1:-1]
                packages[curPack] = []
                continue

            packages[curPack].append(link)

        txt.close()

        # empty packages fix
        for key, value in packages.iteritems():
            if not value:
                packages.pop(key, None)

        if self.getConfig("flush"):
            try:
                txt = open(file, 'wb')
                txt.close()

            except IOError:
                self.logWarning(_("Failed to flush list"))

        for name, links in packages.iteritems():
            self.packages.append((name, links, name))
