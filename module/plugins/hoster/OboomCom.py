# -*- coding: utf-8 -*-

import re
import json

from module.plugins.Hoster import Hoster
from module.plugins.internal.CaptchaService import ReCaptcha

class OboomCom(Hoster):
    __name__ = "OboomCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?oboom\.com/#(?P<ID>[A-Z0-9]{8})/.*'
    __version__ = "0.1"
    __description__ = """oboom.com hoster plugin"""
    __author_name__ = ("stanley")
    __author_mail__ = ("stanley.foerster@gmail.com")

    def loadUrl(self, url):
        self.logDebug("Loading url %s" % url)
        result = json.loads(self.load(url, decode=True))
        self.logDebug("Result: %s" % result)
        return result

    def getFileId(self, url):
        self.fileId = re.match(OboomCom.__pattern__, url).group('ID')

    def getGuestSessionToken(self):
        apiUrl = "http://www.oboom.com/1/guestsession"
        result = self.loadUrl(apiUrl)
        if result[0] == 200:
            self.sessionToken = result[1]
        else:
            self.fail("Could not retrieve token for guest session. Error code %s" % result[0])

    def solveCaptcha(self, token):
        apiUrl = "http://www.oboom.com/1.0/download/config?token=%s" % token
        result = self.loadUrl(apiUrl)

        recaptchaPublickey = ""
        challengeTime = 30

        if result[0] == 200:
            recaptchaPublickey = result[1]["recaptcha"]
            challengeTime = result[1]["waiting"]
        elif result[1] == "blocked_wait":
            self.retry(3, 15*60, "Error: Parallel download running or download limit reached.")
        else:
            self.fail("Could not retrieve captcha information. Error code %s: %s" % (result[0], result[1]))

        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(recaptchaPublickey)
            self.setWait(challengeTime)

            apiUrl = "http://www.oboom.com/1.0/download/ticket?recaptcha_challenge_field=%s" \
                     "&recaptcha_response_field=%s&download_id=%s&token=%s" % \
                     (challenge, response, self.fileId, self.sessionToken)
            result = self.loadUrl(apiUrl)

            if result[0] == 200:
                self.downloadToken = result[1]
                self.downloadAuth = result[2]
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()
        else:
            self.invalidCaptcha()
            self.fail("Received invalid captcha 5 times")

    def getFileInfo(self, token, fileId):
        apiUrl = "http://api.oboom.com/1/ls?token=%s&item=%s" % (token, fileId)
        result = self.loadUrl(apiUrl)
        if result[0] == 200:
            self.fileSize = result[1]["size"]
            self.fileName = result[1]["name"]
            self.fileState = result[1]["state"]
            if not self.fileState == "online":
                self.offline()
        else:
            self.fail("Could not retrieve file info. Error code %s" % result[0])

    def process(self, pyfile):
        self.getGuestSessionToken()
        self.getFileId(self.pyfile.url)
        self.getFileInfo(self.sessionToken, self.fileId)
        self.pyfile.name = self.fileName
        self.pyfile.size = self.fileSize
        self.solveCaptcha(self.sessionToken)

        apiUrl = "http://api.oboom.com/1/dl?token=%s&item=%s&auth=%s" % (self.downloadToken, self.fileId, self.downloadAuth)
        result = self.loadUrl(apiUrl)
        if result[0] == 200:
            self.downloadDomain = result[1]
            self.downloadTicket = result[2]
        else:
            self.fail("Could not retrieve download ticket. Error code %s" % result[0])

        downloadUrl = "http://%s/1.0/dlh?ticket=%s" % (self.downloadDomain, self.downloadTicket)
        self.download(downloadUrl)