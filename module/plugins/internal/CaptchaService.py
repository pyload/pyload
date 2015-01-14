# -*- coding: utf-8 -*-

import re
import time
import base64

from random import random,randint

from module.common.json_layer import json_loads


class CaptchaService:
    __name__    = "CaptchaService"
    __version__ = "0.17"

    __description__ = """Base captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = None

    key = None  #: last key detected


    def __init__(self, plugin):
        self.plugin = plugin


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("%s html not found") % self.__name__
                self.plugin.fail(errmsg)  #@TODO: replace all plugin.fail(errmsg) with plugin.error(errmsg) in 0.4.10
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.plugin.logDebug("%s key: %s" % (self.__name__, self.key))
            return self.key
        else:
            self.plugin.logDebug("%s key not found" % self.__name__)
            return None


    def challenge(self, key=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError


class ReCaptcha(CaptchaService):
    __name__    = "ReCaptcha"
    __version__ = "0.08"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN      = r'recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=([\w-]+)'
    KEY_AJAX_PATTERN = r'Recaptcha\.create\s*\(\s*["\']([\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("ReCaptcha html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html) or re.search(self.KEY_AJAX_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.plugin.logDebug("ReCaptcha key: %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("ReCaptcha key not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("ReCaptcha key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", html).group(1)
            server    = re.search("server : '(.+?)',", html).group(1)
        except:
            errmsg = _("ReCaptcha challenge pattern not found")
            self.plugin.fail(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("ReCaptcha challenge: %s" % challenge)

        return challenge, self.result(server, challenge)


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%simage" % server,
                                            get={'c': challenge},
                                            cookies=True,
                                            forceUser=True,
                                            imgtype="jpg")

        self.plugin.logDebug("ReCaptcha result: %s" % result)

        return result


class ReCaptchaV2(CaptchaService):
    __name__    = "ReCaptchaV2"
    __version__ = "0.01"

    __description__ = """ReCaptchaV2 captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN     = r'data-sitekey="(.*?)">'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("ReCaptcha html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.plugin.logDebug("ReCaptcha key: %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("ReCaptcha key not found")
            return None


    def collectApiInfo(self):
        html = self.plugin.req.load("http://www.google.com/recaptcha/api.js",cookies=True)
        a = re.search("po.src = '(.*?)';",html).group(1)
        vers = a.split("/")[5]
        self.plugin.logDebug("API version: %s" %vers)
        language = a.split("__")[1].split(".")[0]
        self.plugin.logDebug("API language: %s" %language)
              
        html = self.plugin.req.load("https://apis.google.com/js/api.js",cookies=True)
        b = re.search('"h":"(.*?)","',html).group(1)
        jsh = b.decode('unicode-escape')
        self.plugin.logDebug("API jsh-string: %s" %jsh)
        
        return vers,language,jsh
        
    def prepareTimeAndRpc(self):
        html = self.plugin.req.load("http://www.google.com/recaptcha/api2/demo",cookies=True)
        
        millis = int(round(time.time() * 1000))
        self.plugin.logDebug("Systemtime in milliseconds: %s" %str(millis))
        
        rand = randint(1,99999999)
        a = "0.%s"%str(rand*2147483647)
        rpc = int(100000000*float(a))
        self.plugin.logDebug("Self-generated rpc-token: %s" %str(rpc))
        
        return millis,rpc
        
    def doTheCaptcha(self, host):
        self.plugin.logDebug("Parent host: %s" %host)
        botguardstring  = "!A"
        sitekey = self.detect_key()
        vers,language,jsh = self.collectApiInfo()
        millis,rpc = self.prepareTimeAndRpc()

        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/anchor",
                  get={"k":sitekey, 
                       "hl":language, 
                       "v":vers, 
                       "usegapi":"1", 
                       "jsh":jsh+"#id=IO_"+str(millis), 
                       "parent":"http://"+host, 
                       "pfname":"",
                       "rpctoken":rpc},
                  cookies=True)
        recaptchatoken = re.search('id="recaptcha-token" value="(.*?)">',html)
        self.plugin.logDebug("Captchatoken #1: %s" %recaptchatoken.group(1))
            
        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/frame", get={"c":recaptchatoken.group(1),
                                                                                        "hl":language,
                                                                                        "v":vers, 
                                                                                        "bg":botguardstring,
                                                                                        "usegapi":"1", 
                                                                                        "jsh":jsh},
                                                                                   cookies=True)    
        html = html.decode('unicode-escape')
        recaptchatoken2 = re.search('"finput","(.*?)",',html)
        self.plugin.logDebug("Captchatoken #2: %s" %recaptchatoken2.group(1))
        recaptchatoken3 = re.search('."asconf".\s.\s,"(.*?)".',html)
        self.plugin.logDebug("Captchatoken #3: %s" %recaptchatoken3.group(1))
        
        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/reload", post={"c":recaptchatoken2.group(1), 
                                                                                          "reason":"fi", 
                                                                                          "fbg":recaptchatoken3.group(1)},
                                                                                    cookies=True)
        recaptchatoken4 = re.search('"rresp","(.*?)",',html)
        self.plugin.logDebug("Captchatoken #4: %s" %recaptchatoken4.group(1))
            
        millis_captcha_loading = int(round(time.time() * 1000))
        captcha_response = self.plugin.decryptCaptcha("https://www.google.com/recaptcha/api2/payload", get={"c":recaptchatoken4.group(1)},forceUser=True)
        respone_encoded = base64.b64encode('{"response":"%s"}' %captcha_response)
        self.plugin.logDebug("Encoded result: %s" %respone_encoded)
          
        timeToSolve = int(round(time.time() * 1000)) - millis_captcha_loading
        timeToSolveMore = timeToSolve + int(float("0."+str(randint(1,99999999))) * 500)
        html = self.plugin.req.load("https://www.google.com/recaptcha/api2/userverify", cookies=True, post={"c":recaptchatoken4.group(1), 
                                                                                                            "response":respone_encoded, 
                                                                                                            "t":timeToSolve,
                                                                                                            "ct":timeToSolveMore,
                                                                                                            "bg":botguardstring})
        recaptchatoken5 = re.search('"uvresp","(.*?)",',html)
        self.plugin.logDebug("Captchatoken #5: %s" %recaptchatoken5.group(1))
        
        return recaptchatoken5.group(1)


class AdsCaptcha(CaptchaService):
    __name__    = "AdsCaptcha"
    __version__ = "0.06"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    CAPTCHAID_PATTERN  = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*CaptchaId=(\d+)'
    PUBLICKEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*PublicKey=([\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("AdsCaptcha html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())  #: key is the tuple(PublicKey, CaptchaId)
            self.plugin.logDebug("AdsCaptcha key|id: %s | %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("AdsCaptcha key or id not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("AdsCaptcha key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        PublicKey, CaptchaId = key

        html = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx", get={'CaptchaId': CaptchaId, 'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server    = re.search("server: '(.+?)',", html).group(1)
        except:
            errmsg = _("AdsCaptcha challenge pattern not found")
            self.plugin.fail(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("AdsCaptcha challenge: %s" % challenge)

        return challenge, self.result(server, challenge)


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%sChallenge.aspx" % server,
                                            get={'cid': challenge, 'dummy': random()},
                                            cookies=True,
                                            imgtype="jpg")

        self.plugin.logDebug("AdsCaptcha result: %s" % result)

        return result


class SolveMedia(CaptchaService):
    __name__    = "SolveMedia"
    __version__ = "0.06"

    __description__ = """SolveMedia captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'api\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("SolveMedia key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript", get={'k': key})
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
            server    = "http://api.solvemedia.com/papi/media"
        except:
            errmsg = _("SolveMedia challenge pattern not found")
            self.plugin.fail(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("SolveMedia challenge: %s" % challenge)

        return challenge, self.result(server, challenge)


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha(server, get={'c': challenge}, imgtype="gif")

        self.plugin.logDebug("SolveMedia result: %s" % result)

        return result


class AdYouLike(CaptchaService):
    __name__    = "AdYouLike"
    __version__ = "0.02"

    __description__ = """AdYouLike captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    AYL_PATTERN      = r'Adyoulike\.create\s*\((.+?)\)'
    CALLBACK_PATTERN = r'(Adyoulike\.g\._jsonp_\d+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("AdYouLike html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.AYL_PATTERN, html)
        n = re.search(self.CALLBACK_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())
            self.plugin.logDebug("AdYouLike ayl|callback: %s | %s" % self.key)
            return self.key   #: key is the tuple(ayl, callback)
        else:
            self.plugin.logDebug("AdYouLike ayl or callback not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("AdYouLike key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        ayl, callback = key

        # {"adyoulike":{"key":"P~zQ~O0zV0WTiAzC-iw0navWQpCLoYEP"},
        # "all":{"element_id":"ayl_private_cap_92300","lang":"fr","env":"prod"}}
        ayl = json_loads(ayl)

        html = self.plugin.req.load("http://api-ayl.appspot.com/challenge",
                                    get={'key'     : ayl['adyoulike']['key'],
                                         'env'     : ayl['all']['env'],
                                         'callback': callback})
        try:
            challenge = json_loads(re.search(callback + r'\s*\((.+?)\)', html).group(1))
        except:
            errmsg = _("AdYouLike challenge pattern not found")
            self.plugin.fail(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("AdYouLike challenge: %s" % challenge)

        return self.result(ayl, challenge)


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
        except:
            errmsg = _("AdYouLike result not found")
            self.plugin.fail(errmsg)
            raise ValueError(errmsg)

        result = {'_ayl_captcha_engine' : "adyoulike",
                  '_ayl_env'            : server['all']['env'],
                  '_ayl_tid'            : challenge['tid'],
                  '_ayl_token_challenge': challenge['token'],
                  '_ayl_response'       : response}

        self.plugin.logDebug("AdYouLike result: %s" % result)

        return result
