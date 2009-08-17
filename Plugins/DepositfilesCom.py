#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from Plugin import Plugin

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
        self.want_reconnect = False
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_url = urllib.unquote(re.search('<form action="(http://.*\.depositfiles.com/.*)" method="get" onSubmit="download_started', self.html).group(1))
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search('File name: <b title="(.*)">', self.html).group(1)
            return file_name
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights.", self.html) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        
        self.req.download(url, location, cookies=True)
