# -*- coding: utf-8 -*-

import pycurl
import re
import time

from module.common.json_layer import json_loads
from module.plugins.internal.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RapiduNet(SimpleHoster):
    __name__    = "RapiduNet"
    __type__    = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://(?:www\.)?rapidu\.net/(?P<ID>\d{10})'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Rapidu.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", "")]


    COOKIES = [("rapidu.net", "rapidu_lang", "en")]

    INFO_PATTERN    = r'<h1 title="(?P<N>.*)">.*</h1>\s*<small>(?P<S>\d+(\.\d+)?)\s(?P<U>\w+)</small>'
    OFFLINE_PATTERN = r'<h1>404'

    ERROR_PATTERN = r'<div class="error">'

    RECAPTCHA_KEY = r'6Ld12ewSAAAAAHoE6WVP_pSfCdJcBQScVweQh8Io'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = self.premium


    def handleFree(self, pyfile):
        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

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
        response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

        jsvars = self.getJsonResponse("https://rapidu.net/ajax.php",
                                      get={'a': "getCheckCaptcha"},
                                      post={'_go'     : "",
                                            'captcha1': challenge,
                                            'captcha2': response,
                                            'fileId'  : self.info['pattern']['ID']},
                                      decode=True)

        if jsvars['message'] == 'success':
            self.link = jsvars['url']


    def getJsonResponse(self, *args, **kwargs):
        res = self.load(*args, **kwargs)
        if not res.startswith('{'):
            self.retry()

        self.logDebug(res)

        return json_loads(res)


getInfo = create_getInfo(RapiduNet)
