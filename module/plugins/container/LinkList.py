#!/usr/bin/env python
# -*- coding: utf-8 -*-


from module.plugins.Container import Container

class LinkList(Container):
    __name__ = "LinkList"
    __version__ = "0.1"
    __pattern__ = r"(?!http://).*\.txt"
    __description__ = """Read Link Lists in txt format"""
    __author_name__ = ("spoob", "jeix")
    __author_mail__ = ("spoob@pyload.org", "jeix@hasnomail.com")

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.read_config()

    def proceed(self, linkList, location):
        txt = open(linkList, 'r')
        links = txt.readlines()
        packages = {"Parsed links":[],}
        curPack = "Parsed links"
        for link in links:
            if link != "\n":
                link = link.strip()
                if link.startswith(";"):
                    continue
                if link.startswith("[") and link.endswith("]"):
                    # new package
                    curPack = link[1:-1]
                    packages[curPack] = []
                    continue
                packages[curPack].append(link.replace("\n", ""))
        txt.close()
        
        # empty Parsed links fix
        if len(packages["Parsed links"]) < 1:
            del packages["Parsed links"]

        if not self.parent.core.config['general']['debug_mode']:
            txt = open(linkList, 'w')
            txt.write("")
            txt.close()
            #@TODO: maybe delete read txt file?
            
        self.links = packages
