#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.Plugin import Plugin

class DepositfilesCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "DepositfilesCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://depositfiles.com/.{2,}/files/"
        props['version'] = "0.1"
        props['description'] = """Depositfiles.com Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def get_file_url(self):
        return urllib.unquote(re.search('<form action="(http://.+?\.depositfiles.com/.+?)" method="get"', self.html).group(1))

    def get_file_name(self):
        return re.search('File name: <b title="(.*)">', self.html).group(1)

    def file_exists(self):
        self.html = self.req.load(self.parent.url)
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights", self.html) != None:
            return False
        return True
