# -*- coding: utf-8 -*-

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster


class UploadableCh(SimpleHoster):
    __name__    = "UploadableCh"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?uploadable\.ch/file/(?P<ID>\w+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Uploadable.ch hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://www.uploadable.ch/file/\g<ID>')]

    INFO_PATTERN = r'div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>[\d.]+) (?P<U>\w+)\)</span><'

    OFFLINE_PATTERN      = r'>(File not available|This file is no longer available)'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'

    WAIT_PATTERN = r'>Please wait[^<]+'

    RECAPTCHA_KEY = "6LdlJuwSAAAAAPJbPIoUhyqOJd7-yrah5Nhim5S3"


    def handle_free(self, pyfile):
        #: Click the "free user" button and wait
        a = self.load(pyfile.url, post={'downloadLink': "wait"})
        self.log_debug(a)

        self.wait(30)

        #: Make the ReCaptcha appear and show it the pyload interface
        b = self.load(pyfile.url, post={'checkDownload': "check"})
        self.log_debug(b)  #: Expected output: {'success': "showCaptcha"}

        self.captcha = ReCaptcha(pyfile)

        response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

        #: Submit the captcha solution
        self.load("http://www.uploadable.ch/checkReCaptcha.php",
                  post={'recaptcha_challenge_field'  : challenge,
                        'recaptcha_response_field'   : response,
                        'recaptcha_shortencode_field': self.info['pattern']['ID']})

        self.wait(3)

        #: Get ready for downloading
        self.load(pyfile.url, post={'downloadLink': "show"})

        self.wait(3)

        #: Download the file
        self.download(pyfile.url, post={'download': "normal"}, disposition=True)


    def check_download(self):
        if self.scan_download({'wait': re.compile("Please wait for")}):
            self.log_info(_("Downloadlimit reached, please wait or reconnect"))
            self.wait(60 * 60, True)
            self.retry()

        return super(UploadableCh, self).check_download()
