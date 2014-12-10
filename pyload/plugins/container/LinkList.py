# -*- coding: utf-8 -*-

import codecs

from pyload.plugins.Container import Container
from pyload.utils import fs_encode


class LinkList(Container):
    __name    = "LinkList"
    __version = "0.12"

    __pattern = r'.+\.txt'
    __config = [("clear", "bool", "Clear Linklist after adding", False),
                ("encoding", "string", "File encoding (default utf-8)", "")]

    __description = """Read link lists in txt format"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("jeix", "jeix@hasnomail.com")]


    def decrypt(self, pyfile):
        try:
            file_enc = codecs.lookup(self.getConfig("encoding")).name
        except Exception:
            file_enc = "utf-8"

        file_name = fs_encode(pyfile.url)

        txt = codecs.open(file_name, 'r', file_enc)
        links = txt.readlines()
        curPack = "Parsed links from %s" % pyfile.name

        packages = {curPack:[],}

        for link in links:
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

        delete = []

        for key,value in packages.iteritems():
            if not value:
                delete.append(key)

        for key in delete:
            del packages[key]

        if self.getConfig("clear"):
            try:
                txt = open(file_name, 'wb')
                txt.close()
            except Exception:
                self.logWarning(_("LinkList could not be cleared"))

        for name, links in packages.iteritems():
            self.packages.append((name, links, name))
