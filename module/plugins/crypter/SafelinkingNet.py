# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION

from module.lib.BeautifulSoup import BeautifulSoup

from module.common.json_layer import json_loads
from module.plugins.Crypter import Crypter
from module.plugins.internal.CaptchaService import SolveMedia


class SafelinkingNet(Crypter):
    __name__ = "SafelinkingNet"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'https?://(?:www\.)?safelinking.net/([pd])/\w+'

    __description__ = """Safelinking.net decrypter plugin"""
    __author_name__ = "quareevo"
    __author_mail__ = "quareevo@arcor.de"

    SOLVEMEDIA_PATTERN = "solvemediaApiKey = '([\w\.\-_]+)';"


    def decrypt(self, pyfile):
        url = pyfile.url
        if re.match(self.__pattern__, url).group(1) == "d":
            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.load(url)
            m = re.search("^Location: (.+)$", self.req.http.header, re.MULTILINE)
            if m:
                self.urls = [m.group(1)]
            else:
                self.fail("Couldn't find forwarded Link")

        else:
            password = ""
            postData = {"post-protect": "1"}

            self.html = self.load(url)

            if "link-password" in self.html:
                password = pyfile.package().password
                postData['link-password'] = password

            if "altcaptcha" in self.html:
                for _ in xrange(5):
                    m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
                    if m:
                        captchaKey = m.group(1)
                        captcha = SolveMedia(self)
                        captchaProvider = "Solvemedia"
                    else:
                        self.fail("Error parsing captcha")

                    challenge, response = captcha.challenge(captchaKey)
                    postData['adcopy_challenge'] = challenge
                    postData['adcopy_response'] = response

                    self.html = self.load(url, post=postData)
                    if "The password you entered was incorrect" in self.html:
                        self.fail("Incorrect Password")
                    if not "The CAPTCHA code you entered was wrong" in self.html:
                        break

            pyfile.package().password = ""
            soup = BeautifulSoup(self.html)
            scripts = soup.findAll("script")
            for s in scripts:
                if "d_links" in s.text:
                    break
            m = re.search('d_links":(\[.*?\])', s.text)
            if m:
                linkDict = json_loads(m.group(1))
                for link in linkDict:
                    if not "http://" in link['full']:
                        self.urls.append("https://safelinking.net/d/" + link['full'])
                    else:
                        self.urls.append(link['full'])
