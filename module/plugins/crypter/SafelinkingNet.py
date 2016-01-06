# -*- coding: utf-8 -*-

import re

import BeautifulSoup

from module.plugins.internal.utils import json
from module.plugins.internal.Crypter import Crypter, create_getInfo
from module.plugins.captcha.SolveMedia import SolveMedia


class SafelinkingNet(Crypter):
    __name__    = "SafelinkingNet"
    __type__    = "crypter"
    __version__ = "0.18"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?safelinking\.net/([pd])/\w+'
    __config__  = [("activated"         , "bool", "Activated"                          , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("quareevo", "quareevo@arcor.de")]


    SOLVEMEDIA_PATTERN = "solvemediaApiKey = '([\w\-.]+)';"


    def decrypt(self, pyfile):
        url = pyfile.url

        if re.match(self.__pattern__, url).group(1) == "d":

            header = self.load(url, just_header=True)
            if 'location' in header:
                self.urls = [header.get('location')]
            else:
                self.error(_("Couldn't find forwarded Link"))

        else:
            postData = {"post-protect": "1"}

            self.data = self.load(url)

            if "link-password" in self.data:
                postData['link-password'] = self.get_password()

            if "altcaptcha" in self.data:
                m = re.search(self.SOLVEMEDIA_PATTERN, self.data)
                if m is not None:
                    captchaKey = m.group(1)
                    captcha = SolveMedia(self)
                    captchaProvider = "Solvemedia"
                else:
                    self.fail(_("Error parsing captcha"))

                response, challenge = captcha.challenge(captchaKey)
                postData['adcopy_challenge'] = challenge
                postData['adcopy_response']  = response

                self.data = self.load(url, post=postData)

                if "The CAPTCHA code you entered was wrong" in self.data:
                    self.retry_captcha()

                if "The password you entered was incorrect" in self.data:
                    self.fail(_("Wrong password"))

            pyfile.package().password = ""
            soup = BeautifulSoup.BeautifulSoup(self.data)
            scripts = soup.findAll("script")
            for s in scripts:
                if "d_links" in s.text:
                    break
            m = re.search('d_links":(\[.*?\])', s.text)
            if m is not None:
                linkDict = json.loads(m.group(1))
                for link in linkDict:
                    if not "http://" in link['full']:
                        self.urls.append("https://safelinking.net/d/" + link['full'])
                    else:
                        self.urls.append(link['full'])


getInfo = create_getInfo(SafelinkingNet)
