#!/usr/bin/env python
# -*- coding: utf-8 -*-


from module.Plugin import Plugin

class LinkList(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "LinkList"
        props['type'] = "container"
        props['pattern'] = r"(?!http://).*\.txt"
        props['version'] = "0.1"
        props['description'] = """Read Link Lists in txt format"""
        props['author_name'] = ("Spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.read_config()

    def file_exists(self):
        """ returns True or False
        """
        return True

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
            #may delete read txt file?
            
        self.links = tmpLinks
