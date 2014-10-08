# -*- coding: utf-8 -*-
#
# Test links:
# http://www.load.to/JWydcofUY6/random.bin
# http://www.load.to/oeSmrfkXE/random100.bin

import re

from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LoadTo(SimpleHoster):
    __name__ = "LoadTo"
    __type__ = "hoster"
    __version__ = "0.16"

    __pattern__ = r'http://(?:www\.)?load\.to/\w+'

    __description__ = """ Load.to hoster plugin """
    __license__ = "GPLv3"
    __authors__ = [("halfman", "Pulpan3@gmail.com"),
                   ("stickell", "l.stickell@yahoo.it")]


    FILE_NAME_PATTERN = r'<h1>(?P<N>.+)</h1>'
    FILE_SIZE_PATTERN = r'Size: (?P<S>[\d.]+) (?P<U>\w+)'
    OFFLINE_PATTERN = r'>Can\'t find file'

    LINK_PATTERN = r'<form method="post" action="(.+?)"'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'

    FILE_URL_REPLACEMENTS = [(r'(\w)$', r'\1/')]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self):
        # Search for Download URL
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError("Unable to detect download URL")

        download_url = m.group(1)

        # Set Timer - may be obsolete
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1))

        # Load.to is using solvemedia captchas since ~july 2014:
        solvemedia = SolveMedia(self)
        captcha_key = solvemedia.detect_key()

        if captcha_key is None:
            self.download(download_url)
        else:
            captcha_challenge, captcha_response = solvemedia.challenge(captcha_key)
            self.download(download_url, post={"adcopy_challenge": captcha_challenge, "adcopy_response": captcha_response})
            check = self.checkDownload({"404": re.compile("\A<h1>404 Not Found</h1>")})
            if check == "404":
                self.logWarning("The captcha you entered was incorrect. Please try again.")
                self.invalidCaptcha()
                self.retry()


getInfo = create_getInfo(LoadTo)
