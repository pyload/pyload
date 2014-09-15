# -*- coding: utf-8 -*-
#
# Test link:
# http://safesharing.eu/h1ijvcrpl9ys

# Test link (offline):
# http://safesharing.eu/h1ijvcrpl9ysgggggg

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.ReCaptcha import ReCaptcha

class SafesharingEu(SimpleHoster):
    __name__ = "SafesharingEu"
    __type__ = "hoster"
    __version__ = "0.01"
    __pattern__ = r'https?://(?:www\.)?safesharing.eu/\w+'
    __description__ = """Safesharing.eu hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.*)</td></tr>'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>(?P<S>.*) (?P<U>[kKmMbB]*) <small>'
    FILE_ID_PATTERN = r'<input type="hidden" name="id" value="(.*)">'
    FILE_OFFLINE_PATTERN = r'<Title>File Not Found</Title>'
    WAIT_PATTERN = r'You have to wait (\d+) minutes'
    COUNTDOWN_PATTERN = r'<br><span id="countdown_str">Wait <span id=".*">(\d+)</span> seconds</span>'
    RECAPTCHA_KEY_PATTERN = r'<script type="text/javascript" src="http://www.google.com/recaptcha/api/challenge\?k=(.*)"></script>'
    RANDOM_STRING_PATTERN = r'<input type="hidden" name="rand" value="(.*)">'

    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1

    def handleFree(self):
        post_data = {}
        self.html = self.load(self.pyfile.url, cookies=True)
        
        minutes = re.search(self.WAIT_PATTERN, self.html)
        if minutes is not None:
            wait_time = (int(minutes.group(1)) + 1) * 60
            self.logDebug(str(wait_time))
            self.setWait(wait_time,True)
            self.wait()

        recaptcha_key = re.search(self.RECAPTCHA_KEY_PATTERN,self.html)
        if recaptcha_key is not None:
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(re.search(self.RECAPTCHA_KEY_PATTERN,self.html).group(1))
            post_data["recaptcha_challenge_field"] = challenge
            post_data["recaptcha_response_field"] = code
            
        id_num = re.search(self.FILE_ID_PATTERN,self.html)
        rand = re.search(self.RANDOM_STRING_PATTERN,self.html)
        if id_num is None or rand is None:
            self.fail("File-ID or random string not found")
        post_data["rand"] = rand.group(1)
        post_data["id"] = id_num.group(1)
        post_data["op"] = "download2"
        post_data["referer"] = ""
        post_data["method_free"] = ""
        post_data["method_premium"] = ""
        post_data["down_script"] = "1"
        
        countdown = re.search(self.COUNTDOWN_PATTERN, self.html)
        if countdown is not None:
            self.setWait(int(countdown.group(1)))
            self.wait()
            
        self.download(self.pyfile.url, cookies=True, post=post_data, disposition=True)
        check = self.checkDownload({"wrong_captcha": re.compile("recaptcha_response_field"), "is_html": re.compile("html")})
        if check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry()
        elif check == "is_html":
            self.fail("The downloaded file is html, the plugin may be out of date")
        
getInfo = create_getInfo(SafesharingEu)
