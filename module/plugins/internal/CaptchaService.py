# -*- coding: utf-8 -*-

import random
import re
import time
import urlparse

from base64 import b64encode

from module.common.json_layer import json_loads
from module.plugins.Plugin import Base, Fail


#@TODO: Extend (new) Plugin class; remove all `html` args
class CaptchaService(Base):
    __name__    = "CaptchaService"
    __type__    = "captcha"
    __version__ = "0.29"

    __description__ = """Base captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    key = None  #: last key detected


    def __init__(self, plugin):
        self.plugin = plugin
        super(CaptchaService, self).__init__(plugin.core)


    #@TODO: Recheck in 0.4.10
    def fail(self, reason):
        self.plugin.fail(reason)
        raise AttributeError(reason)


    #@TODO: Recheck in 0.4.10
    def retrieve_key(self, html):
        if self.detect_key(html):
            return self.key
        else:
            self.fail(_("%s key not found") % self.__name__)


    #@TODO: Recheck in 0.4.10
    def retrieve_html(self):
        if hasattr(self.plugin, "html") and self.plugin.html:
            return self.plugin.html
        else:
            self.fail(_("%s html not found") % self.__name__)


    def detect_key(self, html=None):
        raise NotImplementedError


    def challenge(self, key=None, html=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError


class AdYouLike(CaptchaService):
    __name__    = "AdYouLike"
    __type__    = "captcha"
    __version__ = "0.06"

    __description__ = """AdYouLike captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    AYL_PATTERN      = r'Adyoulike\.create\s*\((.+?)\)'
    CALLBACK_PATTERN = r'(Adyoulike\.g\._jsonp_\d+)'


    def detect_key(self, html=None):
        html = html or self.retrieve_html()

        m = re.search(self.AYL_PATTERN, html)
        n = re.search(self.CALLBACK_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())
            self.logDebug("Ayl: %s | Callback: %s" % self.key)
            return self.key   #: key is the tuple(ayl, callback)
        else:
            self.logWarning("Ayl or callback pattern not found")
            return None


    def challenge(self, key=None, html=None):
        ayl, callback = key or self.retrieve_key(html)

        # {"adyoulike":{"key":"P~zQ~O0zV0WTiAzC-iw0navWQpCLoYEP"},
        # "all":{"element_id":"ayl_private_cap_92300","lang":"fr","env":"prod"}}
        ayl = json_loads(ayl)

        html = self.plugin.req.load("http://api-ayl.appspot.com/challenge",
                                    get={'key'     : ayl['adyoulike']['key'],
                                         'env'     : ayl['all']['env'],
                                         'callback': callback})
        try:
            challenge = json_loads(re.search(callback + r'\s*\((.+?)\)', html).group(1))

        except AttributeError:
            self.fail(_("AdYouLike challenge pattern not found"))

        self.logDebug("Challenge: %s" % challenge)

        return self.result(ayl, challenge), challenge


    def result(self, server, challenge):
        # Adyoulike.g._jsonp_5579316662423138
        # ({"translations":{"fr":{"instructions_visual":"Recopiez « Soonnight » ci-dessous :"}},
        # "site_under":true,"clickable":true,"pixels":{"VIDEO_050":[],"DISPLAY":[],"VIDEO_000":[],"VIDEO_100":[],
        # "VIDEO_025":[],"VIDEO_075":[]},"medium_type":"image/adyoulike",
        # "iframes":{"big":"<iframe src=\"http://www.soonnight.com/campagn.html\" scrolling=\"no\"
        # height=\"250\" width=\"300\" frameborder=\"0\"></iframe>"},"shares":{},"id":256,
        # "token":"e6QuI4aRSnbIZJg02IsV6cp4JQ9~MjA1","formats":{"small":{"y":300,"x":0,"w":300,"h":60},
        # "big":{"y":0,"x":0,"w":300,"h":250},"hover":{"y":440,"x":0,"w":300,"h":60}},
        # "tid":"SqwuAdxT1EZoi4B5q0T63LN2AkiCJBg5"})

        if isinstance(server, basestring):
            server = json_loads(server)

        if isinstance(challenge, basestring):
            challenge = json_loads(challenge)

        try:
            instructions_visual = challenge['translations'][server['all']['lang']]['instructions_visual']
            result = re.search(u'«(.+?)»', instructions_visual).group(1).strip()

        except AttributeError:
            self.fail(_("AdYouLike result not found"))

        result = {'_ayl_captcha_engine' : "adyoulike",
                  '_ayl_env'            : server['all']['env'],
                  '_ayl_tid'            : challenge['tid'],
                  '_ayl_token_challenge': challenge['token'],
                  '_ayl_response'       : response}

        self.logDebug("Result: %s" % result)

        return result


class AdsCaptcha(CaptchaService):
    __name__    = "AdsCaptcha"
    __type__    = "captcha"
    __version__ = "0.09"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    CAPTCHAID_PATTERN  = r'api\.adscaptcha\.com/Get\.aspx\?.*?CaptchaId=(\d+)'
    PUBLICKEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?.*?PublicKey=([\w-]+)'


    def detect_key(self, html=None):
        html = html or self.retrieve_html()

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())  #: key is the tuple(PublicKey, CaptchaId)
            self.logDebug("Key: %s | ID: %s" % self.key)
            return self.key
        else:
            self.logWarning("Key or id pattern not found")
            return None


    def challenge(self, key=None, html=None):
        PublicKey, CaptchaId = key or self.retrieve_key(html)

        html = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx",
                                    get={'CaptchaId': CaptchaId,
                                         'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server    = re.search("server: '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(_("AdsCaptcha challenge pattern not found"))

        self.logDebug("Challenge: %s" % challenge)

        return self.result(server, challenge), challenge


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%sChallenge.aspx" % server,
                                            get={'cid': challenge, 'dummy': random.random()},
                                            cookies=True,
                                            imgtype="jpg")

        self.logDebug("Result: %s" % result)

        return result


class ReCaptcha(CaptchaService):
    __name__    = "ReCaptcha"
    __type__    = "captcha"
    __version__ = "0.17"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("zapp-brannigan", "fuerst.reinje@web.de")]


    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']:\s*["\'])([\w-]+)'
    KEY_V1_PATTERN = r'(?:recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=|Recaptcha\.create\s*\(\s*["\'])([\w-]+)'


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


class SolveMedia(CaptchaService):
    __name__    = "SolveMedia"
    __type__    = "captcha"
    __version__ = "0.13"

    __description__ = """SolveMedia captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'api\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'


    def detect_key(self, html=None):
        html = html or self.retrieve_html()

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.logDebug("Key: %s" % self.key)
            return self.key
        else:
            self.logWarning("Key pattern not found")
            return None


    def challenge(self, key=None, html=None):
        key = key or self.retrieve_key(html)

        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript",
                                    get={'k': key})

        for i in xrange(1, 11):
            try:
                magic = re.search(r'name="magic" value="(.+?)"', html).group(1)

            except AttributeError:
                self.logWarning("Magic pattern not found")
                magic = None

            try:
                challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="(.+?)">',
                                      html).group(1)

            except AttributeError:
                self.fail(_("SolveMedia challenge pattern not found"))

            else:
                self.logDebug("Challenge: %s" % challenge)

            try:
                result = self.result("http://api.solvemedia.com/papi/media", challenge)

            except Fail, e:
                self.logWarning(e)
                self.plugin.invalidCaptcha()
                result = None

            html = self.plugin.req.load("http://api.solvemedia.com/papi/verify.noscript",
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
                    self.logWarning("Captcha code was invalid")
                    self.logDebug("Retry #%d" % i)
                    html = self.plugin.req.load(redirect)
                else:
                    break

        else:
            self.fail(_("SolveMedia max retries exceeded"))

        return result, challenge


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha(server,
                                            get={'c': challenge},
                                            cookies=True,
                                            imgtype="gif")

        self.logDebug("Result: %s" % result)

        return result
