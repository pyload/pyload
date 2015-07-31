# -*- coding: utf-8 -*-

import random
import re
import time
import urlparse

from base64 import b64encode

from module.plugins.internal.CaptchaService import CaptchaService


class ReCaptcha(CaptchaService):
    __name__    = "ReCaptcha"
    __type__    = "captcha"
    __version__ = "0.18"
    __status__  = "testing"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("zapp-brannigan", "fuerst.reinje@web.de")]


    KEY_V1_PATTERN = r'(?:recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=|Recaptcha\.create\s*\(\s*["\'])([\w-]+)'
    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']:\s*["\'])([\w-]+)'


    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_V2_PATTERN, html) or re.search(self.KEY_V1_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_warning(_("Key pattern not found"))
            return None


    def challenge(self, key=None, data=None, version=None):
        key = key or self.retrieve_key(data)

        if version in (1, 2):
            return getattr(self, "_challenge_v%s" % version)(key)

        else:
            return self.challenge(key,
                                  version=2 if re.search(self.KEY_V2_PATTERN, data or self.retrieve_data()) else 1)


    def _challenge_v1(self, key):
        html = self.plugin.load("http://www.google.com/recaptcha/api/challenge",
                                    get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", html).group(1)
            server    = re.search("server : '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(_("ReCaptcha challenge pattern not found"))

        self.log_debug("Challenge: %s" % challenge)

        return self.result(server, challenge, key)


    def result(self, server, challenge, key):
        self.plugin.load("http://www.google.com/recaptcha/api/js/recaptcha.js")
        html = self.plugin.load("http://www.google.com/recaptcha/api/reload",
                                    get={'c'     : challenge,
                                         'k'     : key,
                                         'reason': "i",
                                         'type'  : "image"})

        try:
            challenge = re.search('\(\'(.+?)\',',html).group(1)

        except AttributeError:
            self.fail(_("ReCaptcha second challenge pattern not found"))

        self.log_debug("Second challenge: %s" % challenge)
        result = self.decrypt(urlparse.urljoin(server, "image"),
                              get={'c': challenge},
                              cookies=True,
                              input_type="jpg")

        self.log_debug("Result: %s" % result)

        return result, challenge


    def _collect_api_info(self):
        html = self.plugin.load("http://www.google.com/recaptcha/api.js")
        a    = re.search(r'po.src = \'(.*?)\';', html).group(1)
        vers = a.split("/")[5]

        self.log_debug("API version: %s" % vers)

        language = a.split("__")[1].split(".")[0]

        self.log_debug("API language: %s" % language)

        html = self.plugin.load("https://apis.google.com/js/api.js")
        b    = re.search(r'"h":"(.*?)","', html).group(1)
        jsh  = b.decode('unicode-escape')

        self.log_debug("API jsh-string: %s" % jsh)

        return vers, language, jsh


    def _prepare_time_and_rpc(self):
        self.plugin.load("http://www.google.com/recaptcha/api2/demo")

        millis = int(round(time.time() * 1000))

        self.log_debug("Time: %s" % millis)

        rand = random.randint(1, 99999999)
        a    = "0.%s" % str(rand * 2147483647)
        rpc  = int(100000000 * float(a))

        self.log_debug("Rpc-token: %s" % rpc)

        return millis, rpc


    def _challenge_v2(self, key, parent=None):
        if parent is None:
            try:
                parent = urlparse.urljoin("http://", urlparse.urlparse(self.plugin.pyfile.url).netloc)

            except Exception:
                parent = ""

        botguardstring      = "!A"
        vers, language, jsh = self._collect_api_info()
        millis, rpc         = self._prepare_time_and_rpc()

        html = self.plugin.load("https://www.google.com/recaptcha/api2/anchor",
                                    get={'k'       : key,
                                         'hl'      : language,
                                         'v'       : vers,
                                         'usegapi' : "1",
                                         'jsh'     : "%s#id=IO_%s" % (jsh, millis),
                                         'parent'  : parent,
                                         'pfname'  : "",
                                         'rpctoken': rpc})

        token1 = re.search(r'id="recaptcha-token" value="(.*?)">', html)
        self.log_debug("Token #1: %s" % token1.group(1))

        html = self.plugin.load("https://www.google.com/recaptcha/api2/frame",
                                get={'c'      : token1.group(1),
                                     'hl'     : language,
                                     'v'      : vers,
                                     'bg'     : botguardstring,
                                     'k'      : key,
                                     'usegapi': "1",
                                     'jsh'    : jsh},
                                decode="unicode-escape")

        token2 = re.search(r'"finput","(.*?)",', html)
        self.log_debug("Token #2: %s" % token2.group(1))

        token3 = re.search(r'"rresp","(.*?)",', html)
        self.log_debug("Token #3: %s" % token3.group(1))

        millis_captcha_loading = int(round(time.time() * 1000))
        captcha_response = self.decrypt("https://www.google.com/recaptcha/api2/payload",
                                              get={'c':token3.group(1), 'k':key},
                                              cookies=True,
                                              ocr=False,
                                              timeout=30)
        response = b64encode('{"response":"%s"}' % captcha_response)

        self.log_debug("Result: %s" % response)

        timeToSolve     = int(round(time.time() * 1000)) - millis_captcha_loading
        timeToSolveMore = timeToSolve + int(float("0." + str(random.randint(1, 99999999))) * 500)

        html = self.plugin.load("https://www.google.com/recaptcha/api2/userverify",
                                    post={'k'       : key,
                                          'c'       : token3.group(1),
                                          'response': response,
                                          't'       : timeToSolve,
                                          'ct'      : timeToSolveMore,
                                          'bg'      : botguardstring})

        token4 = re.search(r'"uvresp","(.*?)",', html)
        self.log_debug("Token #4: %s" % token4.group(1))

        result = token4.group(1)

        return result, None
