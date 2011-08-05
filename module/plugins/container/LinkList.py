#!/usr/bin/env python
# -*- coding: utf-8 -*-


from module.plugins.Container import Container

class LinkList(Container):
    __name__ = "LinkList"
    __version__ = "0.11"
    __pattern__ = r".+\.txt$"
    __description__ = """Read Link Lists in txt format"""
    __config__ = [("clear", "bool", "Clear Linklist after adding", False)]
    __author_name__ = ("spoob", "jeix")
    __author_mail__ = ("spoob@pyload.org", "jeix@hasnomail.com")


    def decrypt(self, pyfile):
        txt = open(pyfile.url, 'r')
        links = txt.readlines()
        curPack = "Parsed links from %s" % pyfile.name
        
        packages = {curPack:[],}
        
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
                txt = open(pyfile.url, 'wb')
                txt.close()
            except:
                self.log.warning(_("LinkList could not be cleared."))
        
        for name, links in packages.iteritems():
            self.packages.append((name, links, name))
