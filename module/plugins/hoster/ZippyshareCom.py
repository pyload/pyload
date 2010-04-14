#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.Plugin import Plugin

class ZippyshareCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "ZippyshareCom"
        props['type'] = "hoster"
        props['pattern'] = r"(http://)?www?\d{0,2}\.zippyshare.com/v/"
        props['version'] = "0.1"
        props['description'] = """Zippyshare.com Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.want_reconnect = False
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        file_url_pattern = r"var \w* = '(http%.*?)';"
        file_url_search = re.search(file_url_pattern, self.html).group(1)
        file_url = urllib.unquote(file_url_search.replace("nnn", "aaa").replace("unlg", "v").replace("serwus", "zippyshare"))
        return file_url
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search("<strong>Name: </strong>(.+?)</font>", self.html).group(1)
            return file_name
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"HTTP Status 404", self.html) != None:
            return False
        else:
            return True
