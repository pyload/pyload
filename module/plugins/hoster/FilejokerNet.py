# -*- coding: utf-8 -*-

import pycurl
import re
import urlparse

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.XFSHoster import XFSHoster


class FilejokerNet(XFSHoster):
    __name__ = "FilejokerNet"
    __type__ = "hoster"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?filejoker\.net/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filejoker.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filejoker.net"

    WAIT_PATTERN = r'[Ww]ait (?:<span id="count" class="alert-success">)?([\w ]+?)(?:</span> seconds</p>| until the next download| to download)'
    ERROR_PATTERN = r'Wrong Captcha|Session expired'

    PREMIUM_ONLY_PATTERN = 'Free Members can download files no bigger'

    INFO_PATTERN = r'<div class="name-size">(?P<N>.+?) <small>\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</small></div>'
    SIZE_REPLACEMENTS = [('Kb', 'KB'), ('Mb', 'MB'), ('Gb', 'GB')]

    LINK_PATTERN = r'<div class="premium-download">\s+<a href="(.+?)"'


    def handle_captcha(self, inputs):
        m = re.search(r'\$\.post\( "/ddl",\s*\{(.+?) \} \);', self.data)
        if m is not None:
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key:
                self.captcha = recaptcha
                response, _ = recaptcha.challenge(captcha_key)

                captcha_inputs = {}
                for _i in m.group(1).split(','):
                    _k, _v = _i.split(':', 1)
                    _k = _k.strip('" ')
                    if _k == "g-recaptcha-response":
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
