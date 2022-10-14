# -*- coding: utf-8 -*-
#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

import re
import urlparse

import pycurl

from ..captcha.HCaptcha import HCaptcha
from ..internal.XFSHoster import XFSHoster


class NovafileCom(XFSHoster):
    __name__ = "NovafileCom"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?novafile\.(?:com|org)/(?:file/)?\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Novafile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it")]

    PLUGIN_DOMAIN = "novafile.com"

    ERROR_PATTERN = r'class="alert.+?alert-separate".*?>\s*(?:<p>)?(.*?)\s*</'
    WAIT_PATTERN = r'<p>Please wait <span id="count".*?>(\d+)</span> seconds</p>'
    DL_LIMIT_PATTERN = r'You have to wait (.+?) until the next download becomes available.'

    LINK_PATTERN = r'<a href="(https://s\d+\.novafile\.(?:com|org)/.*?)" class="btn btn-green">Download File</a>'

    def handle_captcha(self, inputs):
        m = re.search(r'\$\.post\( "/ddl",\s*\{(.+?) \} \);', self.data)
        if m is not None:
            hcaptcha = HCaptcha(self.pyfile)
            captcha_key = hcaptcha.detect_key()
            if captcha_key:
                self.captcha = hcaptcha
                response = hcaptcha.challenge(captcha_key)

                captcha_inputs = {}
                for _i in m.group(1).split(','):
                    _k, _v = _i.split(':', 1)
                    _k = _k.strip('" ')
                    if "g-recaptcha-response" in _v:
                        _v = response

                    captcha_inputs[_k] = _v.strip('" ')

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

                html = self.load(urlparse.urljoin(self.pyfile.url, "/ddl"),
                                 post=captcha_inputs)

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

                if html == "OK":
                    self.captcha.correct()

                else:
                    self.retry_captcha()
