# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilecloudIo(SimpleHoster):
    __name__    = "FilecloudIo"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(?:filecloud\.io|ifile\.it|mihd\.net)/(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Filecloud.io hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    LOGIN_ACCOUNT = True

    NAME_PATTERN         = r'id="aliasSpan">(?P<N>.*?)&nbsp;&nbsp;<'
    SIZE_PATTERN         = r'{var __ab1 = (?P<S>\d+);}'
    OFFLINE_PATTERN      = r'l10n\.(FILES__DOESNT_EXIST|REMOVED)'
    TEMP_OFFLINE_PATTERN = r'l10n\.FILES__WARNING'

    UKEY_PATTERN = r'\'ukey\'\s*:\'(\w+)'
    AB1_PATTERN  = r'if\( __ab1 is \'(\w+)\' \)'

    ERROR_MSG_PATTERN = r'var __error_msg\s*=\s*l10n\.(.*?);'

    RECAPTCHA_PATTERN = r'var __recaptcha_public\s*=\s*\'(.+?)\';'

    LINK_FREE_PATTERN = r'"(http://s\d+\.filecloud\.io/%s/\d+/.*?)"'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        data = {'ukey': self.info['pattern']['ID']}

        m = re.search(self.AB1_PATTERN, self.html)
        if m is None:
            self.error(_("__AB1"))
        data['__ab1'] = m.group(1)

        recaptcha = ReCaptcha(self)

        m = re.search(self.RECAPTCHA_PATTERN, self.html)
        captcha_key = m.group(1) if m else recaptcha.detect_key()

        if captcha_key is None:
            self.error(_("ReCaptcha key not found"))

        response, challenge = recaptcha.challenge(captcha_key)
        self.account.form_data = {'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field' : response}
        self.account.relogin(self.user)
        self.retry(2)

        json_url = "http://filecloud.io/download-request.json"
        res = self.load(json_url, post=data)
        self.log_debug(res)
        res = json_loads(res)

        if "error" in res and res['error']:
            self.fail(res)

        self.log_debug(res)
        if res['captcha']:
            data['ctype'] = "recaptcha"

            for _i in xrange(5):
                data['recaptcha_response'], data['recaptcha_challenge'] = recaptcha.challenge(captcha_key)

                json_url = "http://filecloud.io/download-request.json"
                res = self.load(json_url, post=data)
                self.log_debug(res)
                res = json_loads(res)

                if "retry" in res and res['retry']:
                    self.captcha.invalid()
                else:
                    self.captcha.correct()
                    break
            else:
                self.fail(_("Incorrect captcha"))

        if res['dl']:
            self.html = self.load('http://filecloud.io/download.html')

            m = re.search(self.LINK_FREE_PATTERN % self.info['pattern']['ID'], self.html)
            if m is None:
                self.error(_("LINK_FREE_PATTERN not found"))

            if "size" in self.info and self.info['size']:
                self.check_data = {'size': int(self.info['size'])}

            self.link = m.group(1)
        else:
            self.fail(_("Unexpected server response"))


    def handle_premium(self, pyfile):
        akey = self.account.get_data(self.user)['akey']
        ukey = self.info['pattern']['ID']
        self.log_debug("Akey: %s | Ukey: %s" % (akey, ukey))
        rep = self.load("http://api.filecloud.io/api-fetch_download_url.api",
                        post={'akey': akey, 'ukey': ukey})
        self.log_debug("FetchDownloadUrl: " + rep)
        rep = json_loads(rep)
        if rep['status'] == "ok":
            self.link = rep['download_url']
        else:
            self.fail(rep['message'])


getInfo = create_getInfo(FilecloudIo)
