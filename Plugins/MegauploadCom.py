#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time
from time import sleep

from Plugin import Plugin

class MegauploadCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "MegauploadCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)megaupload.com/"
        props['version'] = "0.1"
        props['description'] = """Megaupload.com Download Plugin"""
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

        captcha_image = tempfile.NamedTemporaryFile(suffix=".gif").name

        for i in range(5):
            self.html[0] = self.req.load(url, cookies=True)
            url_captcha_html = re.search('(http://www.{,3}\.megaupload\.com/gencap.php\?.*\.gif)', self.html[0]).group(1)
            self.req.download(url_captcha_html, captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            captchacode = re.search('name="captchacode" value="(.*)"', self.html[0]).group(1)
            megavar = re.search('name="megavar" value="(.*)">', self.html[0]).group(1)
            self.html[1] = self.req.load(url, post={"captcha": captcha, "captchacode": captchacode, "megavar": megavar}, cookies=True)
            if re.search(r"Waiting time before each download begins", self.html[1]) != None:
                break

        os.remove(captcha_image)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url_pattern = 'id="downloadlink"><a href="(.*)" onclick="'
            search = re.search(file_url_pattern, self.html[1])
            return search.group(1)
        else:
            return False

    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name_pattern = '<font style="font-family:arial; color:#FF6700; font-size:22px; font-weight:bold;">(.*)</font><br>'
            return re.search(file_name_pattern, self.html[0]).group(1)
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r"Unfortunately, the link you have clicked is not available.", self.html[0]) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.req.download(url, location, cookies=True)
