# -*- coding: utf-8 -*-

import re
import time

from pycurl import HTTPHEADER

from pyload.utils import json_loads
from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class RapiduNet(SimpleHoster):
    __name    = "RapiduNet"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'https?://(?:www\.)?rapidu\.net/(?P<ID>\d{10})'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Rapidu.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("prOq", "")]


    COOKIES = [("rapidu.net", "rapidu_lang", "en")]

    INFO_PATTERN    = r'<h1 title="(?P<N>.*)">.*</h1>\s*<small>(?P<S>\d+(\.\d+)?)\s(?P<U>\w+)</small>'
    OFFLINE_PATTERN = r'404 - File not found'

    ERROR_PATTERN = r'<div class="error">'

    RECAPTCHA_KEY = r'6Ld12ewSAAAAAHoE6WVP_pSfCdJcBQScVweQh8Io'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = self.premium


    def handleFree(self, pyfile):
        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        jsvars = self.getJsonResponse("https://rapidu.net/ajax.php",
                                      get={'a': "getLoadTimeToDownload"},
                                      post={'_go': ""},
                                      decode=True)

        if str(jsvars['timeToDownload']) is "stop":
            t = (24 * 60 * 60) - (int(time.time()) % (24 * 60 * 60)) + time.altzone

            self.logInfo("You've reach your daily download transfer")

            self.retry(10, 10 if t < 1 else None, _("Try tomorrow again"))  #@NOTE: check t in case of not synchronised clock

        else:
            self.wait(int(jsvars['timeToDownload']) - int(time.time()))

        recaptcha = ReCaptcha(self)

        for _i in xrange(10):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

            jsvars = self.getJsonResponse("https://rapidu.net/ajax.php",
                                          get={'a': "getCheckCaptcha"},
                                          post={'_go'     : "",
                                                'captcha1': challenge,
                                                'captcha2': response,
                                                'fileId'  : self.info['pattern']['ID']},
                                          decode=True)
            if jsvars['message'] == 'success':
                self.download(jsvars['url'])
                break


    def getJsonResponse(self, *args, **kwargs):
        res = self.load(*args, **kwargs)
        if not res.startswith('{'):
            self.retry()

        self.logDebug(res)

        return json_loads(res)
