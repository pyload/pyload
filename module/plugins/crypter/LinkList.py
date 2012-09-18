#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter, Package

class LinkList(Crypter):
    __name__ = "LinkList"
    __version__ = "0.11"
    __pattern__ = r".+\.txt$"
    __description__ = """Read Link Lists in txt format"""
    __author_name__ = ("spoob", "jeix")
    __author_mail__ = ("spoob@pyload.org", "jeix@hasnomail.com")

    # method declaration is needed here
    def decryptURL(self, url):
        return Crypter.decryptURL(self, url)

    def decryptFile(self, content):
        links = content.splitlines()

        curPack = "default"
        packages = {curPack:[]}
        
        for link in links:
            link = link.strip()
            if not link: continue
            
            if link.startswith(";"):
                continue
            if link.startswith("[") and link.endswith("]"):
                # new package
                curPack = link[1:-1]
                packages[curPack] = []
                continue
            packages[curPack].append(link)
        
        # empty packages fix
        delete = []
        
        for key,value in packages.iteritems():
            if not value:
                delete.append(key)
                
        for key in delete:
            del packages[key]

        urls = []

        for name, links in packages.iteritems():
            if name == "default":
                urls.extend(links)
            else:
                urls.append(Package(name, links))

        return urls