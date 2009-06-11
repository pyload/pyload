#!/usr/bin/env python

import re
from Plugin import Plugin

class XupIn(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "XupIn"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)?xup.in/"
        props['version'] = "0.1"
        props['description'] = """Xup.in Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.posts = {}
        self.want_reconnect = None
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)
        self.posts["vid"] = re.search('"hidden" value="(.*)" name="vid"', self.html).group(1)
        self.posts["vtime"] = re.search('"hidden" value="(.*)" name="vtime"', self.html).group(1)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_url_pattern = r".*<form action=\"(.*)\" method=\"post\">"
            return re.search(file_url_pattern, self.html).group(1)
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            return self.parent.url.split('/')[-2]
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.*<font color=\"#ff0000\">File does not exist</font>.*)", self.html, re.I) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.req.download(url, location, self.posts)

    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
