#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import random
import re
import tempfile
import urllib2

from module.Plugin import Plugin
from module.network.MultipartPostHandler import MultipartPostHandler

class CCF(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "CCF"
        props['type'] = "container"
        props['pattern'] = r".*\.ccf"
        props['version'] = "0.1"
        props['description'] = """CCF Container Convert Plugin"""
        props['author_name'] = ("Willnix")
        props['author_mail'] = ("Willnix@pyload.org")
        self.props = props
        self.parent = parent
        self.multi_dl = True
        self.links = []

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        infile = url.replace("\n", "")

        opener = urllib2.build_opener(MultipartPostHandler)
        params = {"src": "ccf",
            "filename": "test.ccf",
            "upload": open(infile, "rb")}
        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', params).read()

        random.seed()
        tempdir = tempfile.gettempdir()
        if tempdir[0] == '/':
            delim = '/'
        else:
            delim = '\\'
        tempdlc_name = tempdir + delim + str(random.randint(0, 100)) + '-tmp.dlc'
        while os.path.exists(tempdlc_name):
            tempdlc_name = tempfile.gettempdir() + '/' + str(random.randint(0, 100)) + '-tmp.dlc'

        tempdlc = open(tempdlc_name, "w")
        tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
        tempdlc.close

        self.links.append(tempdlc_name)

        return True
