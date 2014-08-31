# -*- coding: utf-8 -*-
#
# Test links:
# https://www.oboom.com/B7CYZIEB/10Mio.dat

import re

from module.common.json_layer import json_loads
from module.plugins.Hoster import Hoster
from module.plugins.internal.CaptchaService import ReCaptcha


class OboomCom(Hoster):
    __name__ = "OboomCom"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'https?://(?:www\.)?oboom\.com/(#(id=|/)?)?(?P<ID>[A-Z0-9]{8})'

    __description__ = """oboom.com hoster plugin"""
    __author_name__ = "stanley"
    __author_mail__ = "stanley.foerster@gmail.com"

    RECAPTCHA_KEY = "6LdqpO0SAAAAAJGHXo63HyalP7H4qlRs_vff0kJX"


    def loadUrl(self, url, get=None):
        if get is None:
            get = dict()
        return json_loads(self.load(url, get, decode=True))

    def getFileId(self, url):
        self.fileId = re.match(OboomCom.__pattern__, url).group('ID')

    def getSessionToken(self):
        if self.premium:
            accountInfo = self.account.getAccountInfo(self.user, True)
            if "session" in accountInfo:
                self.sessionToken = accountInfo['session']
            else:
                self.fail("Could not retrieve premium session")
        else:
            apiUrl = "https://www.oboom.com/1.0/guestsession"
            result = self.loadUrl(apiUrl)
            if result[0] == 200:
                self.sessionToken = result[1]
            else:
                self.fail("Could not retrieve token for guest session. Error code %s" % result[0])

    def solveCaptcha(self):
        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            apiUrl = "https://www.oboom.com/1.0/download/ticket"
            params = {"recaptcha_challenge_field": challenge,
                      "recaptcha_response_field": response,
                      "download_id": self.fileId,
                      "token": self.sessionToken}
            result = self.loadUrl(apiUrl, params)

            if result[0] == 200:
                self.downloadToken = result[1]
                self.downloadAuth = result[2]
                self.correctCaptcha()
                self.setWait(30)
                self.wait()
                break
            elif result[0] == 400:
                if result[1] == "incorrect-captcha-sol":
                    self.invalidCaptcha()
                elif result[1] == "captcha-timeout":
                    self.invalidCaptcha()
                elif result[1] == "forbidden":
                    self.retry(5, 15 * 60, "Service unavailable")
            elif result[0] == 403:
                if result[1] == -1:  # another download is running
                    self.setWait(15 * 60)
                else:
                    self.setWait(result[1], reconnect=True)
                self.wait()
                self.retry(5)
        else:
            self.invalidCaptcha()
            self.fail("Received invalid captcha 5 times")

    def getFileInfo(self, token, fileId):
        apiUrl = "https://api.oboom.com/1.0/info"
        params = {"token": token, "items": fileId, "http_errors": 0}

        result = self.loadUrl(apiUrl, params)
        if result[0] == 200:
            item = result[1][0]
            if item['state'] == "online":
                self.fileSize = item['size']
                self.fileName = item['name']
            else:
                self.offline()
        else:
            self.fail("Could not retrieve file info. Error code %s: %s" % (result[0], result[1]))

    def getDownloadTicket(self):
        apiUrl = "https://api.oboom.com/1.0/dl"
        params = {"item": self.fileId, "http_errors": 0}
        if self.premium:
            params['token'] = self.sessionToken
        else:
            params['token'] = self.downloadToken
            params['auth'] = self.downloadAuth

        result = self.loadUrl(apiUrl, params)
        if result[0] == 200:
            self.downloadDomain = result[1]
            self.downloadTicket = result[2]
        else:
            self.fail("Could not retrieve download ticket. Error code %s" % result[0])

    def setup(self):
        self.chunkLimit = 1
        self.multiDL = self.premium

    def process(self, pyfile):
        self.pyfile.url.replace(".com/#id=", ".com/#")
        self.pyfile.url.replace(".com/#/", ".com/#")
        self.getFileId(self.pyfile.url)
        self.getSessionToken()
        self.getFileInfo(self.sessionToken, self.fileId)
        self.pyfile.name = self.fileName
        self.pyfile.size = self.fileSize
        if not self.premium:
            self.solveCaptcha()
        self.getDownloadTicket()
        self.download("https://%s/1.0/dlh" % self.downloadDomain, get={"ticket": self.downloadTicket, "http_errors": 0})
