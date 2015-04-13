# -*- coding: utf-8 -*-

import re

from pyload.plugin.Captcha import Captcha


class SolveMedia(Captcha):
    __name__    = "SolveMedia"
    __type__    = "captcha"
    __version__ = "0.12"

    __description__ = """SolveMedia captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'api\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("SolveMedia html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.logDebug("Key: %s" % self.key)
            return self.key
        else:
            self.logDebug("Key not found")
            return None


    def challenge(self, key=None, html=None):
        if not key:
            if self.detect_key(html):
                key = self.key
            else:
                errmsg = _("SolveMedia key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript",
                                    get={'k': key})
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
            server    = "http://api.solvemedia.com/papi/media"

        except AttributeError:
            errmsg = _("SolveMedia challenge pattern not found")
            self.plugin.fail(errmsg)
            raise AttributeError(errmsg)

        self.logDebug("Challenge: %s" % challenge)

        result = self.result(server, challenge)

        try:
            magic = re.search(r'name="magic" value="(.+?)"', html).group(1)

        except AttributeError:
            self.logDebug("Magic code not found")

        else:
            if not self._verify(key, magic, result, challenge):
                self.logDebug("Captcha code was invalid")

        return result, challenge


    def _verify(self, key, magic, result, challenge, ref=None):  #@TODO: Clean up
        if ref is None:
            try:
                ref = self.plugin.pyfile.url

            except Exception:
                ref = ""

        html = self.plugin.req.load("http://api.solvemedia.com/papi/verify.noscript",
                                    post={'adcopy_response'  : result,
                                          'k'                : key,
                                          'l'                : "en",
                                          't'                : "img",
                                          's'                : "standard",
                                          'magic'            : magic,
                                          'adcopy_challenge' : challenge,
                                          'ref'              : ref})
        try:
            html      = self.plugin.req.load(re.search(r'URL=(.+?)">', html).group(1))
            gibberish = re.search(r'id=gibberish>(.+?)</textarea>', html).group(1)

        except Exception:
            return False

        else:
            return True


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha(server,
                                            get={'c': challenge},
                                            cookies=True,
                                            imgtype="gif")

        self.logDebug("Result: %s" % result)

        return result
