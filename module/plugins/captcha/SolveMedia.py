# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Plugin import Fail
from module.plugins.internal.CaptchaService import CaptchaService


class SolveMedia(CaptchaService):
    __name__    = "SolveMedia"
    __type__    = "captcha"
    __version__ = "0.15"
    __status__  = "testing"

    __description__ = """SolveMedia captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'api\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'


    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_warning(_("Key pattern not found"))
            return None


    def challenge(self, key=None, data=None):
        key = key or self.retrieve_key(data)

        html = self.plugin.load("http://api.solvemedia.com/papi/challenge.noscript",
                                    get={'k': key})

        for i in xrange(1, 11):
            try:
                magic = re.search(r'name="magic" value="(.+?)"', html).group(1)

            except AttributeError:
                self.log_warning(_("Magic pattern not found"))
                magic = None

            try:
                challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="(.+?)">',
                                      html).group(1)

            except AttributeError:
                self.fail(_("SolveMedia challenge pattern not found"))

            else:
                self.log_debug("Challenge: %s" % challenge)

            try:
                result = self.result("http://api.solvemedia.com/papi/media", challenge)

            except Fail, e:
                self.log_warning(e)
                self.plugin.invalidCaptcha()
                result = None

            html = self.plugin.load("http://api.solvemedia.com/papi/verify.noscript",
                                        post={'adcopy_response' : result,
                                              'k'               : key,
                                              'l'               : "en",
                                              't'               : "img",
                                              's'               : "standard",
                                              'magic'           : magic,
                                              'adcopy_challenge': challenge,
                                              'ref'             : self.plugin.pyfile.url})
            try:
                redirect = re.search(r'URL=(.+?)">', html).group(1)

            except AttributeError:
                self.fail(_("SolveMedia verify pattern not found"))

            else:
                if "error" in html:
                    self.log_warning(_("Captcha code was invalid"))
                    self.log_debug("Retry #%d" % i)
                    html = self.plugin.load(redirect)
                else:
                    break

        else:
            self.fail(_("SolveMedia max retries exceeded"))

        return result, challenge


    def result(self, server, challenge):
        result = self.decrypt(server,
                                    get={'c': challenge},
                                    cookies=True,
                                    input_type="gif")

        self.log_debug("Result: %s" % result)

        return result
