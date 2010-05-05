#!/usr/bin/env python
# -*- coding: utf-8 -*-


from module.plugins.Container import Container

class LinkList(Container):
    __name__ = "LinkList"
    __version__ = "0.1"
    __pattern__ = r"(?!http://).*\.txt"
    __description__ = """Read Link Lists in txt format"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.read_config()

    def proceed(self, linkList, location):
        tmpLinks = []
        txt = open(linkList, 'r')
        links = txt.readlines()
        for link in links:
            if link != "\n":
                tmpLinks.append(link.replace("\n", ""))
        txt.close()

        if not self.parent.core.config['general']['debug_mode']:
            txt = open(linkList, 'w')
            txt.write("")
            txt.close()
            #@TODO: maybe delete read txt file?
            
        self.links = tmpLinks
