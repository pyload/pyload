# -*- coding: utf-8 -*-

import re

from time import sleep

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadableCh(SimpleHoster):
    __name__    = "UploadableCh"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?uploadable\.ch/file/(?P<ID>\w+)'

    __description__ = """Uploadable.ch hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://www.uploadable.ch/file/\g<ID>')]

    FILE_INFO_PATTERN = r'div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>[\d.]+) (?P<U>\w+)\)</span><'

    OFFLINE_PATTERN      = r'>(File not available|This file is no longer available)'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'

    WAIT_PATTERN = r'>Please wait.+?<'

    RECAPTCHA_KEY = "6LdlJuwSAAAAAPJbPIoUhyqOJd7-yrah5Nhim5S3"


    def setup(self):
        self.multiDL    = False
        self.chunkLimit = 1


    def handleFree(self):
        # Click the "free user" button and wait
        a = self.load(self.pyfile.url, cookies=True, post={'downloadLink': "wait"}, decode=True)
        self.logDebug(a)

        self.wait(30)

        # Make the recaptcha appear and show it the pyload interface
        b = self.load(self.pyfile.url, cookies=True, post={'checkDownload': "check"}, decode=True)
        self.logDebug(b)  #: Expected output: {"success":"showCaptcha"}

        recaptcha = ReCaptcha(self)

        challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)

        # Submit the captcha solution
        self.load("http://www.uploadable.ch/checkReCaptcha.php",
                  cookies=True,
                  post={'recaptcha_challenge_field'  : challenge,
                        'recaptcha_response_field'   : response,
                        'recaptcha_shortencode_field': self.info['pattern']['ID']},
                  decode=True)

        self.wait(3)

        # Get ready for downloading
        self.load(self.pyfile.url, cookies=True, post={'downloadLink': "show"}, decode=True)

        self.wait(3)

        # Download the file
        self.download(self.pyfile.url, cookies=True, post={'download': "normal"}, disposition=True)


    def checkFile(self):
        super(UploadableCh, self).checkFile()

        check = self.checkDownload({'wait_or_reconnect': re.compile("Please wait for"),
                                    'is_html'          : re.compile("<head>")})

        if check == "wait_or_reconnect":
            self.logInfo("Downloadlimit reached, please wait or reconnect")
            self.wait(60 * 60, True)
            self.retry()

        elif check == "is_html":
            self.error("Downloaded file is an html file")


getInfo = create_getInfo(UploadableCh)
