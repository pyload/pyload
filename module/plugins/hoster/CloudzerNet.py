#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.network.RequestFactory import getURL
from module.utils import parseFileSize


def getInfo(urls):
    for url in urls:
        header = getURL(url, just_header=True)
        if 'Location: http://cloudzer.net/404' in header:
            file_info = (url, 0, 1, url)
        else:
            fid = re.search(CloudzerNet.__pattern__, url).group('ID')
            api_data = getURL('http://cloudzer.net/file/%s/status' % fid)
            name, size = api_data.splitlines()
            size = parseFileSize(size)
            file_info = (name, size, 2, url)
        yield file_info


class CloudzerNet(SimpleHoster):
    __name__ = "CloudzerNet"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)(?P<ID>\w+).*"
    __version__ = "0.04"
    __description__ = """Cloudzer.net hoster plugin"""
    __author_name__ = ("gs", "z00nx", "stickell")
    __author_mail__ = ("I-_-I-_-I@web.de", "z00nx0@gmail.com", "l.stickell@yahoo.it")

    WAIT_PATTERN = '<meta name="wait" content="(\d+)">'
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
        response = json_loads(self.load('http://cloudzer.net/io/ticket/captcha/%s' % self.file_info['ID'],
                                        post=post_data, cookies=True))
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

    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)

        header = getURL(self.pyfile.url, just_header=True)

        if 'Location: http://cloudzer.net/404' in header:
            self.offline()
        else:
            self.fid = re.search(self.__pattern__, self.pyfile.url).group('ID')
            api_data = getURL('http://cloudzer.net/file/%s/status' % self.fid)
            self.pyfile.name, size = api_data.splitlines()
            self.pyfile.size = parseFileSize(size)

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (self.pyfile.name, self.pyfile.size))
