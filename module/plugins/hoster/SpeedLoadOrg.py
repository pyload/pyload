# -*- coding: utf-8 -*-
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha
import re


def getInfo(urls):
    for url in urls:
        header = getURL(url, just_header=True)
        if 'Location: http://speedload.org/index.php' in header:
            file_info = (url, 0, 1, url)
        else:
            file_info = parseFileInfo(SpeedLoadOrg, url, getURL(url, decode=True))
        yield file_info


class SpeedLoadOrg(SimpleHoster):
    __name__ = "SpeedLoadOrg"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?speedload\.org/(?P<ID>\w+).*"
    __version__ = "0.01"
    __description__ = """Speedload.org hoster plugin"""
    __author_name__ = ("z00nx")
    __author_mail__ = ("z00nx0@gmail.com")

    FILE_NAME_PATTERN = '<div class="d_file[^>]+>\s+<div>\s+<div[^>]+>(?P<N>[^<]+)</div>'
    FILE_SIZE_PATTERN = 'File Size:&nbsp;</span>(?P<S>[^<]+)</span>'
    RECAPTCHA_KEY = '6LenSdkSAAAAAJyoP5jFZl4NNell2r4rzfXRZXGW'

    def handleFree(self):
        recaptcha = ReCaptcha(self)
        self.load
        challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
        post_data = {'recaptcha_challenge_field': challenge, 'recaptcha_response_field': response, 'submit': 'continue', 'submitted': '1', 'd': '1'}
        self.download(self.pyfile.url, post=post_data)
        check = self.checkDownload({"html": re.compile("\A<!DOCTYPE html PUBLIC")})
        if check == "html":
            self.logDebug("Wrong captcha entered")
            self.invalidCaptcha()
            self.retry()
