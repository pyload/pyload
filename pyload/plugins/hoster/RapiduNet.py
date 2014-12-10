# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER
from time import time, altzone

from pyload.utils import json_loads
from pyload.plugins.captcha import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RapiduNet(SimpleHoster):
    __name__    = "RapiduNet"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?rapidu\.net/(?P<ID>\d{10})'

    __description__ = """Rapidu.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", None)]


    COOKIES = [("rapidu.net", "rapidu_lang", "en")]

    FILE_INFO_PATTERN = r'<h1 title="(?P<N>.*)">.*</h1>\s*<small>(?P<S>\d+(\.\d+)?)\s(?P<U>\w+)</small>'
    OFFLINE_PATTERN   = r'404 - File not found'

    ERROR_PATTERN = r'<div class="error">'

    RECAPTCHA_KEY = r'6Ld12ewSAAAAAHoE6WVP_pSfCdJcBQScVweQh8Io'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True
        self.limitDL        = 0 if self.premium else 2


    def handleFree(self):
        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        jsvars = self.getJsonResponse("https://rapidu.net/ajax.php?a=getLoadTimeToDownload", {'_go': None})

        if str(jsvars['timeToDownload']) is "stop":
            t = (24 * 60 * 60) - (int(time()) % (24 *60 * 60)) + altzone

            self.logInfo("You've reach your daily download transfer")

            self.retry(10,  10 if t < 1 else None, "Try tomorrow again")  #@NOTE: check t in case of not synchronised clock

        else:
            self.wait(int(jsvars['timeToDownload']) - int(time()))

        recaptcha = ReCaptcha(self)

        for _i in xrange(10):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)

            jsvars = self.getJsonResponse("https://rapidu.net/ajax.php?a=getCheckCaptcha",
                                          {'_go'     : None,
                                           'captcha1': challenge,
                                           'captcha2': response,
                                           'fileId'  : self.info['ID']})
            if jsvars['message'] == 'success':
                self.download(jsvars['url'])
                break


    def getJsonResponse(self, url, post_data):
        res = self.load(url, post=post_data, decode=True)
        if not res.startswith('{'):
            self.retry()

        self.logDebug(url, res)

        return json_loads(res)


getInfo = create_getInfo(RapiduNet)
