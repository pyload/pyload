#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import sleep

from module.plugins.Plugin import Plugin

class DDLMusicOrg(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "DDLMusicOrg"
        props['type'] = "container"
        props['pattern'] = r"http://[\w\.]*?ddl-music\.org/captcha/ddlm_cr\d\.php\?\d+\?\d+"
        props['version'] = "0.1"
        props['description'] = """ddl-music.org Container Plugin"""
        props['author_name'] = ("mkaay")
        props['author_mail'] = ("mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url, cookies=True)

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()
        if re.search(r"Wer dies nicht rechnen kann", self.html) != None:
            return True
        return False

    def proceed(self, url, location):
        for i in range(5):
            self.download_html()
            posturl = re.search(r"id=\"captcha\" action=\"(/captcha/ddlm_cr\d\.php)\"", self.html).group(1)
            math = re.search(r"(\d+) ([\+-]) (\d+) =\s+<inp", self.html)
            id = re.search(r"name=\"id\" value=\"(\d+)\"", self.html).group(1)
            linknr = re.search(r"name=\"linknr\" value=\"(\d+)\"", self.html).group(1)
            
            solve = ""
            if math.group(2) == "+":
                solve = int(math.group(1)) + int(math.group(3))
            else:
                solve = int(math.group(1)) - int(math.group(3))
            sleep(3)
            htmlwithlink = self.req.load("http://ddl-music.org%s" % posturl, cookies=True, post={"calc%s" % linknr:solve, "send%s" % linknr:"Send", "id":id, "linknr":linknr})
            m = re.search(r"<form id=\"ff\" action=\"(.*?)\" method=\"post\">", htmlwithlink)
            if m:
                self.links = [m.group(1)]
                return
        self.links = False
