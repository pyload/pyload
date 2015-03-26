# -*- coding: utf-8 -*-

import re

from pyload.plugin.captcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class UploadableCh(SimpleHoster):
    __name    = "UploadableCh"
    __type    = "hoster"
    __version = "0.09"

    __pattern = r'http://(?:www\.)?uploadable\.ch/file/(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Uploadable.ch hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern + ".*", r'http://www.uploadable.ch/file/\g<ID>')]

    INFO_PATTERN = r'div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>[\d.]+) (?P<U>\w+)\)</span><'

    OFFLINE_PATTERN      = r'>(File not available|This file is no longer available)'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'

    WAIT_PATTERN = r'>Please wait.+?<'

    RECAPTCHA_KEY = "6LdlJuwSAAAAAPJbPIoUhyqOJd7-yrah5Nhim5S3"


    def handleFree(self, pyfile):
        # Click the "free user" button and wait
        a = self.load(pyfile.url, post={'downloadLink': "wait"}, decode=True)
        self.logDebug(a)

        self.wait(30)

        # Make the recaptcha appear and show it the pyload interface
        b = self.load(pyfile.url, post={'checkDownload': "check"}, decode=True)
        self.logDebug(b)  #: Expected output: {"success":"showCaptcha"}

        recaptcha = ReCaptcha(self)

        response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

        # Submit the captcha solution
        self.load("http://www.uploadable.ch/checkReCaptcha.php",
                  post={'recaptcha_challenge_field'  : challenge,
                        'recaptcha_response_field'   : response,
                        'recaptcha_shortencode_field': self.info['pattern']['ID']},
                  decode=True)

        self.wait(3)

        # Get ready for downloading
        self.load(pyfile.url, post={'downloadLink': "show"}, decode=True)

        self.wait(3)

        # Download the file
        self.download(pyfile.url, post={'download': "normal"}, disposition=True)


    def checkFile(self, rules={}):
        if self.checkDownload({'wait': re.compile("Please wait for")}):
            self.logInfo("Downloadlimit reached, please wait or reconnect")
            self.wait(60 * 60, True)
            self.retry()

        return super(UploadableCh, self).checkFile(rules)
