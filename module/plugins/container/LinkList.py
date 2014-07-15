# -*- coding: utf-8 -*-

import codecs

from module.plugins.Container import Container
from module.utils import fs_encode


class LinkList(Container):
    __name__ = "LinkList"
    __version__ = "0.12"

    __pattern__ = r'.+\.txt'
    __config__ = [("clear", "bool", "Clear Linklist after adding", False),
                  ("encoding", "string", "File encoding (default utf-8)", "")]

    __description__ = """Read link lists in txt format"""
    __author_name__ = ("spoob", "jeix")
    __author_mail__ = ("spoob@pyload.org", "jeix@hasnomail.com")


    def decrypt(self, pyfile):
        try:
            file_enc = codecs.lookup(self.getConfig("encoding")).name
        except:
            file_enc = "utf-8"

        print repr(pyfile.url)
        print pyfile.url

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
            except:
                self.logWarning(_("LinkList could not be cleared."))

        for name, links in packages.iteritems():
            self.packages.append((name, links, name))
