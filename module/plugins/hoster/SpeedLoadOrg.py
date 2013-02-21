# -*- coding: utf-8 -*-
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha
from module.common.json_layer import json_loads
import re


def getInfo(urls):
    for url in urls:
        api_data = getAPIData(url)
        online = False if 'File Not Found' in api_data else True
        if online:
            file_info = (api_data['originalFilename'], api_data['size'], 2 , url)
        else:
            file_info = (url, 0, 1 , url)
        yield file_info

def getAPIData(url):
    API_URL = 'http://speedload.org/api/single_link.php?shortUrl='

    file_id = re.search(SpeedLoadOrg.__pattern__, url).group('ID')
    api_data = json_loads(getURL(API_URL + file_id, decode = True))
    if isinstance(api_data, dict):
        api_data['size'] = api_data['fileSize']

    return api_data


class SpeedLoadOrg(SimpleHoster):
    __name__ = "SpeedLoadOrg"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?speedload\.org/(?P<ID>\w+).*"
    __version__ = "0.06"
    __description__ = """Speedload.org hoster plugin"""
    __author_name__ = ("z00nx", "stickell")
    __author_mail__ = ("z00nx0@gmail.com", "l.stickell@yahoo.it")

    FILE_NAME_PATTERN = '<div class="d_file[^>]+>\s+<div>\s+<div[^>]+>(?P<N>[^<]+)</div>'
    FILE_SIZE_PATTERN = 'File Size:&nbsp;</span>(?P<S>[^<]+)</span>'
    FILE_OFFLINE_PATTERN = '<div class="promo" style="[^"]+">'
    RECAPTCHA_KEY = '6LenSdkSAAAAAJyoP5jFZl4NNell2r4rzfXRZXGW'

    def handleFree(self):
        self.api_data = getAPIData(self.pyfile.url)
        recaptcha = ReCaptcha(self)
        challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
        post_data = {'recaptcha_challenge_field': challenge, 'recaptcha_response_field': response, 'submit': 'continue', 'submitted': '1', 'd': '1'}
        self.download(self.pyfile.url, post=post_data)
        check = self.checkDownload({
            "html": re.compile("\A<!DOCTYPE html PUBLIC"),
            "busy": "You are already downloading a file. Please upgrade to premium.",
            "socket": "Could not open socket"})
        if check == "html":
            self.logDebug("Wrong captcha entered")
            self.invalidCaptcha()
            self.retry()
        elif check == "busy":
            self.retry(10, 300, "Already downloading")
        elif check == "socket":
            self.fail("Server error: Could not open socket")
