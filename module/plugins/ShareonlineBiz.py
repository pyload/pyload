#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time
from base64 import b64decode

from Plugin import Plugin

class ShareonlineBiz(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "ShareonlineBiz"
        props['type'] = "hoster"
        props['pattern'] = r"(?:http://)?(?:www.)?share-online.biz/download.php\?id="
        props['version'] = "0.1"
        props['description'] = """Shareonline.biz Download Plugin"""
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
            self.req.download("http://www.share-online.biz/captcha.php", captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            self.html[1] = self.req.load(url, post={"captchacode": captcha}, cookies=True)
            if re.search(r"Der Download ist Ihnen zu langsam?", self.html[1]) != None:
                self.time_plus_wait = time() + 15
                break

        os.remove(captcha_image)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url_pattern = 'loadfilelink\.decode\("(.*==)"\);'
            return b64decode(re.search(file_url_pattern, self.html[1]).group(1))
        else:
            return False

    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name_pattern = 'class="locatedActive">Download (.*)</span>'
            return re.search(file_name_pattern, self.html[1]).group(1)
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r"nicht zum Download bereitgestellt werden", self.html[0]) != None:
            return False
        else:
            return True
