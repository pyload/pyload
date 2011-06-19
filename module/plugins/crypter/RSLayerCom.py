#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter
from module.lib.BeautifulSoup import BeautifulSoup
from module.unescape import unescape

class RSLayerCom(Crypter):
    __name__ = "RSLayerCom"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?rs-layer.com/directory-"
    __config__ = []
    __version__ = "0.2"
    __description__ = """RS-Layer.com Container Plugin"""
    __author_name__ = ("hzpz")
    __author_mail__ = ("none")

    def decrypt(self, pyfile):
        url = pyfile.url
        src = self.req.load(str(url))

        soup = BeautifulSoup(src)
        captchaTag = soup.find("img", attrs={"id": "captcha_image"})
        if captchaTag:
            captchaUrl = "http://rs-layer.com/" + captchaTag["src"]
            self.logDebug("Captcha URL: %s" % captchaUrl)
            result = self.decryptCaptcha(str(captchaUrl), imgtype="png")
            captchaInput = soup.find("input", attrs={"id": "captcha"})
            self.req.lastUrl = url
            src = self.req.load(str(url), post={'captcha_input': result, 'image_name': captchaTag["src"]})

        link_ids = re.findall(r"onclick=\"getFile\(\'([0-9]{7}-.{8})\'\);changeBackgroundColor", src)

        if not len(link_ids) > 0:
            self.retry()

        self.correctCaptcha()

        links = []
        for id in link_ids:
            self.logDebug("ID: %s" % id)
            new_link = unescape(re.search(r"<iframe style=\"width: 100%; height: 100%;\" src=\"(.*)\"></frame>",
                                          self.req.load("http://rs-layer.com/link-" + id + ".html")).group(1))
            self.logDebug("Link: %s" % new_link)
            links.append(new_link)

        self.packages.append((self.pyfile.package().name, links, self.pyfile.package().folder))
