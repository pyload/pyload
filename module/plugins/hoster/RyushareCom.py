# -*- coding: utf-8 -*-
#
# Test links:
# http://ryushare.com/cl0jy8ric2js/random.bin

import re

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from module.plugins.internal.CaptchaService import SolveMedia


class RyushareCom(XFileSharingPro):
    __name__ = "RyushareCom"
    __type__ = "hoster"
    __version__ = "0.15"

    __pattern__ = r'http://(?:www\.)?ryushare\.com/\w+'

    __description__ = """Ryushare.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell", "quareevo")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it", "quareevo@arcor.de")

    HOSTER_NAME = "ryushare.com"

    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[\d\.]+) (?P<U>\w+)'

    WAIT_PATTERN = r'You have to wait ((?P<hour>\d+) hour[s]?, )?((?P<min>\d+) minute[s], )?(?P<sec>\d+) second[s]'
    LINK_PATTERN = r'(http://([^/]*?ryushare.com|\d+\.\d+\.\d+\.\d+)(:\d+/d/|/files/\w+/\w+/)[^"\'<]+)'
    SOLVEMEDIA_PATTERN = r'http:\/\/api\.solvemedia\.com\/papi\/challenge\.script\?k=(.*?)"'


    def getDownloadLink(self):
        retry = False
        self.html = self.load(self.pyfile.url)
        action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})
        if "method_premium" in inputs:
            del inputs['method_premium']

        self.html = self.load(self.pyfile.url, post=inputs)
        action, inputs = self.parseHtmlForm('F1')

        self.setWait(65)
        # Wait 1 hour
        if "You have reached the download-limit" in self.html:
            self.setWait(1 * 60 * 60, True)
            retry = True

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait = m.groupdict(0)
            waittime = int(wait['hour']) * 60 * 60 + int(wait['min']) * 60 + int(wait['sec'])
            self.setWait(waittime, True)
            retry = True

        self.wait()
        if retry:
            self.retry()

        for _ in xrange(5):
            m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
            if m is None:
                self.parseError("Error parsing captcha")

            captchaKey = m.group(1)
            captcha = SolveMedia(self)
            challenge, response = captcha.challenge(captchaKey)

            inputs['adcopy_challenge'] = challenge
            inputs['adcopy_response'] = response

            self.html = self.load(self.pyfile.url, post=inputs)
            if "WRONG CAPTCHA" in self.html:
                self.invalidCaptcha()
                self.logInfo("Invalid Captcha")
            else:
                self.correctCaptcha()
                break
        else:
            self.fail("You have entered 5 invalid captcha codes")

        if "Click here to download" in self.html:
            return re.search(r'<a href="([^"]+)">Click here to download</a>', self.html).group(1)


getInfo = create_getInfo(RyushareCom)
