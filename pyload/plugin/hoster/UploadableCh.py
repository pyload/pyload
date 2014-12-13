# -*- coding: utf-8 -*-

import re

from time import sleep

from pyload.plugin.captcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadableCh(SimpleHoster):
    __name    = "UploadableCh"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?uploadable\.ch/file/(?P<ID>\w+)'

    __description = """Uploadable.ch hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_INFO_PATTERN = r'div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>[\d.]+) (?P<U>\w+)\)</span><'

    OFFLINE_PATTERN      = r'>(File not available|This file is no longer available)'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'

    WAIT_PATTERN = r'data-time="(\d+)" data-format'

    FILE_URL_REPLACEMENTS = [(__pattern + ".*", r'http://www.uploadable.ch/file/\g<ID>')]


    def setup(self):
        self.multiDL    = False
        self.chunkLimit = 1


    def handleFree(self):
        # Click the "free user" button and wait
        a = self.load(self.pyfile.url, cookies=True, post={'downloadLink': "wait"}, decode=True)
        self.logDebug(a)

        m = re.search(self.WAIT_PATTERN, a)
        if m is not None:
            self.wait(int(m.group(1)))  #: Expected output: {"waitTime":30}
        else:
            self.error("WAIT_PATTERN")

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
                        'recaptcha_shortencode_field': self.info['ID']},
                  decode=True)

        self.wait(3)

        # Get ready for downloading
        self.load(self.pyfile.url, cookies=True, post={'downloadLink': "show"}, decode=True)

        self.wait(3)

        # Download the file
        self.download(self.pyfile.url, cookies=True, post={'download': "normal"}, disposition=True)


    def checkFile(self):
        check = self.checkDownload({'wait_or_reconnect': re.compile("Please wait for"),
                                    'is_html'          : re.compile("<head>")})

        if check == "wait_or_reconnect":
            self.logInfo("Downloadlimit reached, please wait or reconnect")
            self.wait(60 * 60, True)
            self.retry()

        elif check == "is_html":
            self.error("Downloaded file is an html file")


getInfo = create_getInfo(UploadableCh)
