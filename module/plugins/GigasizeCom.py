#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time

from module.Plugin import Plugin

class GigasizeCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "GigasizeCom"
        props['type'] = "hoster"
        props['pattern'] = r"(?:http://)?(?:www.)?gigasize.com/get.php\?d="
        props['version'] = "0.1"
        props['description'] = """Gigasize.com Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = [None, None]
        self.want_reconnect = False
        self.init_ocr()
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html[0] = self.req.load(url, cookies=True)

        captcha_image = tempfile.NamedTemporaryFile(suffix=".jpg").name

        for i in range(5):
            self.req.download("http://www.gigasize.com/randomImage.php", captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            self.html[1] = self.req.load("http://www.gigasize.com/formdownload.php", None, {"txtNumber": captcha}, cookies=True)

            if re.search(r"Package features", self.html[1]) != None:
                if re.search(r"YOU HAVE REACHED YOUR HOURLY LIMIT", self.html[1]) != None:
                    self.time_plus_wait = time() + 3600 #one hour
                #self.time_plus_wait = time() + 60
                break

        os.remove(captcha_image)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url_pattern = '<form action="(/getcgi.php\?t=.*)" method="post" id="formDownload">'
            search = re.search(file_url_pattern, self.html[1])
            if search:
                return "http://gigazise.com" + search.group(1)
            return ""
        else:
            return False

    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name_pattern = "<p><strong>Name</strong>: <b>(.*)</b></p>"
            return re.search(file_name_pattern, self.html[0]).group(1)
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r"The file has been deleted", self.html[0]) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        print url
        print self.req.load(url, cookies=True)
