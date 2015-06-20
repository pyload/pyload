# -*- coding: utf-8 -*-

import random
import re
import time
import urlparse

from base64 import b64encode

from module.plugins.internal.Captcha import Captcha


class ReCaptcha(Captcha):
    __name__    = "ReCaptcha"
    __type__    = "captcha"
    __version__ = "0.17"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("zapp-brannigan", "fuerst.reinje@web.de")]


    KEY_V1_PATTERN = r'(?:recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=|Recaptcha\.create\s*\(\s*["\'])([\w-]+)'
    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']:\s*["\'])([\w-]+)'


    def detect_key(self, html=None):
        html = html or self.retrieve_html()

        m = re.search(self.KEY_V2_PATTERN, html) or re.search(self.KEY_V1_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.logDebug("Key: %s" % self.key)
            return self.key
        else:
            self.logWarning("Key pattern not found")
            return None


    def challenge(self, key=None, html=None, version=None):
        key = key or self.retrieve_key(html)

        if version in (1, 2):
            return getattr(self, "_challenge_v%s" % version)(key)

        else:
            return self.challenge(key,
                                  version=2 if re.search(self.KEY_V2_PATTERN, html or self.retrieve_html()) else 1)


    def _challenge_v1(self, key):
        html = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge",
                                    get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", html).group(1)
            server    = re.search("server : '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(_("ReCaptcha challenge pattern not found"))

        self.logDebug("Challenge: %s" % challenge)

        return self.result(server, challenge, key)


    def result(self, server, challenge, key):
        self.plugin.req.load("http://www.google.com/recaptcha/api/js/recaptcha.js")
        html = self.plugin.req.load("http://www.google.com/recaptcha/api/reload",
                                    get={'c'     : challenge,
                                         'k'     : key,
                                         'reason': "i",
                                         'type'  : "image"})

        try:
            challenge = re.search('\(\'(.+?)\',',html).group(1)

        except AttributeError:
            self.fail(_("ReCaptcha second challenge pattern not found"))

        self.logDebug("Second challenge: %s" % challenge)
        result = self.plugin.decryptCaptcha("%simage" % server,
                                            get={'c': challenge},
                                            cookies=True,
                                            forceUser=True,
                                            imgtype="jpg")

        self.logDebug("Result: %s" % result)

        return result, challenge


    def _collectApiInfo(self):
        html = self.plugin.req.load("http://www.google.com/recaptcha/api.js")
        a    = re.search(r'po.src = \'(.*?)\';', html).group(1)
        vers = a.split("/")[5]

        self.logDebug("API version: %s" % vers)

        language = a.split("__")[1].split(".")[0]

        self.logDebug("API language: %s" % language)

        html = self.plugin.req.load("https://apis.google.com/js/api.js")
        b    = re.search(r'"h":"(.*?)","', html).group(1)
        jsh  = b.decode('unicode-escape')

        self.logDebug("API jsh-string: %s" % jsh)

        return vers, language, jsh


    def _prepareTimeAndRpc(self):
        self.plugin.req.load("http://www.google.com/recaptcha/api2/demo")

        millis = int(round(time.time() * 1000))

        self.logDebug("Time: %s" % millis)

        rand = random.randint(1, 99999999)
        a    = "0.%s" % str(rand * 2147483647)
        rpc  = int(100000000 * float(a))

        self.logDebug("Rpc-token: %s" % rpc)

        return millis, rpc


    def _challenge_v2(self, key, parent=None):
        if parent is None:
            try:
                parent = urlparse.urljoin("http://", urlparse.urlparse(self.plugin.pyfile.url).netloc)

            except Exception:
                parent = ""

        botguardstring      = "!A"
        vers, language, jsh = self._collectApiInfo()
        millis, rpc         = self._prepareTimeAndRpc()

        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/anchor",
                                    get={'k'       : key,
                                         'hl'      : language,
                                         'v'       : vers,
                                         'usegapi' : "1",
                                         'jsh'     : "%s#id=IO_%s" % (jsh, millis),
                                         'parent'  : parent,
                                         'pfname'  : "",
                                         'rpctoken': rpc})

        token1 = re.search(r'id="recaptcha-token" value="(.*?)">', html)
        self.logDebug("Token #1: %s" % token1.group(1))

        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/frame",
                                    get={'c'      : token1.group(1),
                                         'hl'     : language,
                                         'v'      : vers,
                                         'bg'     : botguardstring,
                                         'k'      : key,
                                         'usegapi': "1",
                                         'jsh'    : jsh}).decode('unicode-escape')

        token2 = re.search(r'"finput","(.*?)",', html)
        self.logDebug("Token #2: %s" % token2.group(1))

        token3 = re.search(r'"rresp","(.*?)",', html)
        self.logDebug("Token #3: %s" % token3.group(1))

        millis_captcha_loading = int(round(time.time() * 1000))
        captcha_response = self.plugin.decryptCaptcha("https://www.google.com/recaptcha/api2/payload",
                                                      get={'c':token3.group(1), 'k':key},
                                                      cookies=True,
                                                      forceUser=True)
        response = b64encode('{"response":"%s"}' % captcha_response)

        self.logDebug("Result: %s" % response)

        timeToSolve     = int(round(time.time() * 1000)) - millis_captcha_loading
        timeToSolveMore = timeToSolve + int(float("0." + str(random.randint(1, 99999999))) * 500)

        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/userverify",
                                    post={'k'       : key,
                                          'c'       : token3.group(1),
                                          'response': response,
                                          't'       : timeToSolve,
                                          'ct'      : timeToSolveMore,
                                          'bg'      : botguardstring})

        token4 = re.search(r'"uvresp","(.*?)",', html)
        self.logDebug("Token #4: %s" % token4.group(1))

        result = token4.group(1)

        return result, None
