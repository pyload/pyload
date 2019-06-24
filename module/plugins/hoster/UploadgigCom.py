# -*- coding: utf-8 -*-

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class UploadgigCom(SimpleHoster):
    __name__ = "UploadgigCom"
    __type__ = "hoster"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?uploadgig.com/file/download/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Uploadgig.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [("http://", "https://")]

    NAME_PATTERN = r'<span class="filename">(?P<N>.+?)<'
    SIZE_PATTERN = r'<span class="filesize">\[(?P<S>[\d.,]+) (?P<U>[\w^_]+)\]<'

    OFFLINE_PATTERN = r'File not found'

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('id="dl_captcha_form"')
        if inputs is None:
            self.error(_("Free download form not found"))

        recaptcha = ReCaptcha(pyfile)

        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            self.error(_("ReCaptcha key not found"))

        self.captcha = recaptcha
        response, challenge = recaptcha.challenge(captcha_key)

        inputs['g-recaptcha-response'] = response
        self.data = self.load(self.fixurl(url),
                              post=inputs)

        if self.data == "m":
            self.log_warning(_("Max downloads for this hour reached"))
            self.retry(wait=60*60)

        elif self.data in ("fl", "rfd"):
            self.fail(_("File can be downloaded by premium users only"))

        elif self.data == "e":
            self.retry()

        elif self.data == "0":
            self.retry_captcha()

        else:
            try:
                res = json.loads(self.data)

            except:
                self.fail(_("Illegal response from the server"))

            if any([_x not in res for _x in ('cd', 'fopg', 'fghre')]):
                self.fail(_("Illegal response from the server"))

            self.wait(res['cd'])

            self.link = "http://" + res['fopg'] + res['fghre'] +"/dlfile"
