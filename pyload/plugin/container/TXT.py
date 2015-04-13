# -*- coding: utf-8 -*-

import codecs

from pyload.plugin.Container import Container
from pyload.utils import fs_encode


class TXT(Container):
    __name    = "TXT"
    __type    = "container"
    __version = "0.15"

    __pattern = r'.+\.(txt|text)$'
    __config  = [("flush"   , "bool"  , "Flush list after adding", False  ),
                 ("encoding", "string", "File encoding"          , "utf-8")]

    __description = """Read link lists in plain text formats"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                     ("jeix", "jeix@hasnomail.com")]


    def decrypt(self, pyfile):
        try:
            encoding = codecs.lookup(self.getConfig('encoding')).name

        except Exception:
            encoding = "utf-8"

        fs_filename = fs_encode(pyfile.url.strip())
        txt         = codecs.open(fs_filename, 'r', encoding)
        curPack     = "Parsed links from %s" % pyfile.name
        packages    = {curPack:[],}

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

        if self.getConfig('flush'):
            try:
                txt = open(fs_filename, 'wb')
                txt.close()

            except IOError:
                self.logWarning(_("Failed to flush list"))

        for name, links in packages.iteritems():
            self.packages.append((name, links, name))
