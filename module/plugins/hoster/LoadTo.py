# -*- coding: utf-8 -*-
#
# Test links:
# http://www.load.to/JWydcofUY6/random.bin
# http://www.load.to/oeSmrfkXE/random100.bin

import re

from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LoadTo(SimpleHoster):
    __name__    = "LoadTo"
    __type__    = "hoster"
    __version__ = "0.18"

    __pattern__ = r'http://(?:www\.)?load\.to/\w+'

    __description__ = """ Load.to hoster plugin """
    __license__     = "GPLv3"
    __authors__     = [("halfman", "Pulpan3@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    NAME_PATTERN = r'<h1>(?P<N>.+)</h1>'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>Can\'t find file'

    LINK_PATTERN = r'<form method="post" action="(.+?)"'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'

    URL_REPLACEMENTS = [(r'(\w)$', r'\1/')]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self):
        # Search for Download URL
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))

        download_url = m.group(1)

        # Set Timer - may be obsolete
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(int(m.group(1)))

        # Load.to is using solvemedia captchas since ~july 2014:
        solvemedia = SolveMedia(self)
        captcha_key = solvemedia.detect_key()

        if captcha_key is None:
            self.download(download_url)
        else:
            challenge, response = solvemedia.challenge(captcha_key)

            self.download(download_url, post={"adcopy_challenge": challenge, "adcopy_response": response})

            check = self.checkDownload({'404': re.compile("\A<h1>404 Not Found</h1>"), 'html': re.compile("html")})

            if check == "404":
                self.invalidCaptcha()
                self.retry()
            elif check == "html":
                self.logWarning(_("Downloaded file is an html page, will retry"))
                self.retry()


getInfo = create_getInfo(LoadTo)
