# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION

from BeautifulSoup import BeautifulSoup

from pyload.utils import json_loads
from pyload.plugins.internal.Crypter import Crypter
from pyload.plugins.internal.captcha import SolveMedia


class SafelinkingNet(Crypter):
    __name__    = "SafelinkingNet"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'https?://(?:www\.)?safelinking\.net/([pd])/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("quareevo", "quareevo@arcor.de")]


    SOLVEMEDIA_PATTERN = "solvemediaApiKey = '([\w.-]+)';"


    def decrypt(self, pyfile):
        url = pyfile.url

        if re.match(self.__pattern__, url).group(1) == "d":

            header = self.load(url, just_header=True)
            if 'location' in header:
                self.urls = [header['location']]
            else:
                self.error(_("Couldn't find forwarded Link"))

        else:
            postData = {"post-protect": "1"}

            if "link-password" in self.html:
                postData['link-password'] = self.getPassword()

            if "altcaptcha" in self.html:
                for _i in xrange(5):
                    m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
                    if m:
                        captchaKey = m.group(1)
                        captcha = SolveMedia(self)
                        captchaProvider = "Solvemedia"
                    else:
                        self.fail(_("Error parsing captcha"))

                    challenge, response = captcha.challenge(captchaKey)
                    postData['adcopy_challenge'] = challenge
                    postData['adcopy_response']  = response

                    self.html = self.load(url, post=postData)
                    if "The password you entered was incorrect" in self.html:
                        self.fail(_("Incorrect Password"))
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
