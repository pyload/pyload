# -*- coding: utf-8 -*-

import re
from pycurl import FOLLOWLOCATION

from module.common.json_layer import json_loads
from module.plugins.Crypter import Crypter
from module.plugins.internal.CaptchaService import SolveMedia
from module.lib.BeautifulSoup import BeautifulSoup


class SafelinkingNet(Crypter):
    __name__ = 'SafelinkingNet'
    __type__ = 'crypter'
    __pattern__ = r'https?://safelinking.net/([pd])/\w+'
    __version__ = '0.1'
    __description__ = 'Safelinking.net Crypter Plugin'
    __author_name__ = 'quareevo'
    __author_mail__ = 'quareevo@arcor.de'

    __Solvemedia_pattern__ = "solvemediaApiKey = '([\w\.\-_]+)';"

    def decrypt(self, pyfile):
        url = pyfile.url
        if re.search(self.__pattern__, url).group(1) == "d":
            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.load(url)
            m = re.search("^Location: (.+)$", self.req.http.header, re.MULTILINE)
            if m:
                self.core.files.addLinks([m.group(1)], self.pyfile.package().id)
            else:
                self.fail("Couldn't find forwarded Link")

        else:
            password = ""
            packageLinks = []
            postData = {"post-protect": "1"}

            self.html = self.load(url)

            if "link-password" in self.html:
                password = pyfile.package().password
                postData["link-password"] = password

            if "altcaptcha" in self.html:
                for i in xrange(5):
                    m = re.search(self.__Solvemedia_pattern__, self.html)
                    if m:
                        captchaKey = m.group(1)
                        captcha = SolveMedia(self)
                        captchaProvider = "Solvmedia"
                    else:
                        self.fail("Error parsing captcha")

                    challenge, response = captcha.challenge(captchaKey)
                    postData["adcopy_challenge"] = challenge
                    postData["adcopy_response"] = response

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
                    if not "http://" in link["full"]:
                        packageLinks.append("https://safelinking.net/d/" + link["full"])
                    else:
                        packageLinks.append(link["full"])

            self.core.files.addLinks(packageLinks, self.pyfile.package().id)
