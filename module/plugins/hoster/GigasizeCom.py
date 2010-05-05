#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time

from module.plugins.Hoster import Hoster

class GigasizeCom(Hoster):
    __name__ = "GigasizeCom"
    __type__ = "hoster"
    __pattern__ = r"(?:http://)?(?:www.)?gigasize.com/get.php\?d="
    __version__ = "0.1"
    __description__ = """Gigasize.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = [None, None]
        self.want_reconnect = False
        self.init_ocr()
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html[0] = self.load(url, cookies=True)

        captcha_image = tempfile.NamedTemporaryFile(suffix=".jpg").name

        for i in range(5):
            self.download("http://www.gigasize.com/randomImage.php", captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            self.html[1] = self.load("http://www.gigasize.com/formdownload.php", None, {"txtNumber": captcha}, cookies=True)

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
