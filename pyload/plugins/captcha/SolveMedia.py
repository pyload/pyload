# -*- coding: utf-8 -*-

import re

from pyload.plugins.base.Captcha import Captcha


class SolveMedia(Captcha):
    __name__ = "SolveMedia"
    __version__ = "0.02"

    __description__ = """SolveMedia captcha service plugin"""
    __author_name__ = "pyLoad Team"
    __author_mail__ = "admin@pyload.org"


    KEY_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.(no)?script\?k=(?P<KEY>.+?)"'


    def challenge(self, key=None):
        if not key:
            if self.key:
                key = self.key
            else:
                errmsg = "SolveMedia key missing"
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript", get={'k': key}, cookies=True)
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
            server = "http://api.solvemedia.com/papi/media"
        except:
            self.plugin.parseError("SolveMedia challenge pattern not found")

        result = self.result(server, challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha(server, get={'c': challenge}, imgtype="gif")
