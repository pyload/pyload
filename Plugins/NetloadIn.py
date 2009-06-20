#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time

from Plugin import Plugin

class NetloadIn(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "NetloadIn"
        props['type'] = "hoster"
        props['pattern'] = r"(?:http://)?(?:www.)?http://netload.in/"
        props['version'] = "0.1"
        props['description'] = """Netload.in Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = [None, None, None]
        self.want_reconnect = False
        self.init_ocr()
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html[0] = self.req.load(url, cookies=True)
        url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', self.html[0]).group(1).replace("amp;", "")

        self.html[1] = self.req.load(url_captcha_html, cookies=True)
        captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', self.html[1]).group(1)
        file_id = re.search('<input name="file_id" type="hidden" value="(.*)" />', self.html[1]).group(1)

        captcha_image = tempfile.NamedTemporaryFile(suffix=".png").name

        for i in range(5):
            self.req.download(captcha_url, captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            self.html[2] = self.req.load("http://netload.in/index.php?id=10", post={"file_id": file_id, "captcha_check": captcha}, cookies=True)
            if re.search(r"download:", self.html[2]) != None:
                self.time_plus_wait = time() + 20
                break

        os.remove(captcha_image)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url_pattern = '<a class="Orange_Link" href="(http://.+)" >Click here'
            search = re.search(file_url_pattern, self.html[2])
            if search:
                return search.group(1)
            return ""
        else:
            return False

    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name_pattern = '\t\t\t(.+)<span style="color: #8d8d8d;">'
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
        self.req.download(url, location, cookies=True)
