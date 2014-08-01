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
    __version__ = "0.15"

    __pattern__ = r'http://(?:www\.)?load\.to/\w+'

    __description__ = """Load.to hoster plugin"""
    __author_name__ = ("halfman", "stickell")
    __author_mail__ = ("Pulpan3@gmail.com", "l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'<head><title>(?P<N>.+) \/\/ Load.to</title>'
    FILE_SIZE_PATTERN = r'<a [^>]+>(?P<Z>.+)</a></h3>\s*Size: (?P<S>.*) (?P<U>[kKmMgG]?i?[bB])'
    OFFLINE_PATTERN = r'Can\'t find file\. Please check URL'

    LINK_PATTERN = r'<form method="post" action="(.+?)"'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.noscript\?k=([^"]+)'


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
        m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
        if m is None:
            self.download(download_url)
        else:
            captcha_key = m.group(1)
            solvemedia = SolveMedia(self)
            captcha_challenge, captcha_response = solvemedia.challenge(captcha_key)
            self.download(download_url, post={"adcopy_challenge": captcha_challenge, "adcopy_response": captcha_response})
            check = self.checkDownload({"404": re.compile("\A<h1>404 Not Found</h1>")})
            if check == "404":
                self.logWarning("The captcha you entered was incorrect. Please try again.")
                self.invalidCaptcha()
                self.retry()


getInfo = create_getInfo(LoadTo)
