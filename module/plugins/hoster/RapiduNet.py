# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER
from module.common.json_layer import json_loads
from time import time, altzone

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RapiduNet(SimpleHoster):
    __name__ = "RapiduNet"
    __type__ = "hoster"
    __version__ = "0.01"
    __pattern__ = r'https?://(?:www\.)?rapidu\.net/(?P<fileID>\d{10})(/|/.*)?'
    __description__ = """Rapidu.net hoster plugin"""
    __authors__ = [("prOq", None)]


    FILE_INFO_PATTERN = r'<h1 title="(?P<N>.*)">.*</h1>\s*<small>(?P<S>\d+(\.\d+)?)\s(?P<U>\w+)</small>'

    OFFLINE_PATTERN = '404 - (File not found|Nie znaleziono pliku)'
    ERROR_PATTERN = '<div class="error">'

    RECAPTCHA_KEY = r'6Ld12ewSAAAAAHoE6WVP_pSfCdJcBQScVweQh8Io'

    fileID = ""


    def setup(self):
        self.resumeDownload = True
	self.multiDL = True

	if self.premium:
	    self.limitDL = -1
	else:
	    self.limitDL = 2


    def process(self, pyfile):
	m = re.match(self.__pattern__, self.pyfile.url)
	if m:
	    self.fileID = m.group('fileID')
	else:
	    self.fail("URL mismatch")

        self.handleFree()


    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

	if re.search(self.ERROR_PATTERN, self.html):
	    self.fail("An error occured on hoster")

        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        jsvars = self.getJsonResponse("https://rapidu.net/ajax.php?a=getLoadTimeToDownload", {"_go": None})

	if str(jsvars['timeToDownload']) is "stop":
	    t = (24 *60 * 60) - (int(time()) % (24 *60 * 60)) + altzone
	    t = 10 if t < 1 else None	# in case of not synchronised clock
	    self.logInfo("You've reach your daily download transfer")
	    self.retry(10, t, "Try tomorrow again")
	else:
	    self.wait((int(jsvars['timeToDownload'])-int(time())))

	recaptcha = ReCaptcha(self)

	for _ in xrange(10):
	    challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)

            self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
            jsvars = self.getJsonResponse("https://rapidu.net/ajax.php?a=getCheckCaptcha", {
			"_go": None,
			"captcha1": challenge,
			"captcha2": code,
			"fileId": self.fileID
			})

	    if jsvars['message'] == 'success':
		self.download(jsvars['url'])
		break


    def getJsonResponse(self, url, post_data):
        response = self.load(url, post=post_data, decode=True)
        if not response.startswith('{'):
            self.retry()
        self.logDebug(url, response)
        return json_loads(response)


getInfo = create_getInfo(RapiduNet)
