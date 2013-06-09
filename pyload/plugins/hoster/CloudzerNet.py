# -*- coding: utf-8 -*-
import re
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.common.json_layer import json_loads
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getURL


def getInfo(urls):
    for url in urls:
        header = getURL(url, just_header=True)
        if 'Location: http://cloudzer.net/404' in header:
            file_info = (url, 0, 1, url)
        else:
            file_info = parseFileInfo(CloudzerNet, url, getURL(url, decode=True))
        yield file_info


class CloudzerNet(SimpleHoster):
    __name__ = "CloudzerNet"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)(?P<ID>\w+).*"
    __version__ = "0.02"
    __description__ = """Cloudzer.net hoster plugin"""
    __author_name__ = ("gs", "z00nx")
    __author_mail__ = ("I-_-I-_-I@web.de", "z00nx0@gmail.com")

    FILE_SIZE_PATTERN = '<span class="size">(?P<S>[^<]+)</span>'
    WAIT_PATTERN = '<meta name="wait" content="(\d+)">'
    FILE_OFFLINE_PATTERN = r'Please check the URL for typing errors, respectively'
    CAPTCHA_KEY = '6Lcqz78SAAAAAPgsTYF3UlGf2QFQCNuPMenuyHF3'

    def handleFree(self):
        found = re.search(self.WAIT_PATTERN, self.html)
        seconds = int(found.group(1))
        self.logDebug("Found wait", seconds)
        self.setWait(seconds + 1)
        self.wait()
        response = self.load('http://cloudzer.net/io/ticket/slot/%s' % self.file_info['ID'], post=' ', cookies=True)
        self.logDebug("Download slot request response", response)
        response = json_loads(response)
        if response["succ"] is not True:
            self.fail("Unable to get a download slot")

        recaptcha = ReCaptcha(self)
        challenge, response = recaptcha.challenge(self.CAPTCHA_KEY)
        post_data = {"recaptcha_challenge_field": challenge, "recaptcha_response_field": response}
        response = json_loads(self.load('http://cloudzer.net/io/ticket/captcha/%s' % self.file_info['ID'], post=post_data, cookies=True))
        self.logDebug("Captcha check response", response)
        self.logDebug("First check")

        if "err" in response:
            if response["err"] == "captcha":
                self.logDebug("Wrong captcha")
                self.invalidCaptcha()
                self.retry()
            elif "Sie haben die max" in response["err"] or "You have reached the max" in response["err"]:
                self.logDebug("Download limit reached, waiting an hour")
                self.setWait(3600, True)
                self.wait()
        if "type" in response:
            if response["type"] == "download":
                url = response["url"]
                self.logDebug("Download link", url)
                self.download(url, disposition=True)
