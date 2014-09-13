# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilecloudIo(SimpleHoster):
    __name__ = "FilecloudIo"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?(?:filecloud\.io|ifile\.it|mihd\.net)/(?P<ID>\w+).*'

    __description__ = """Filecloud.io hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    FILE_SIZE_PATTERN = r'{var __ab1 = (?P<S>\d+);}'
    FILE_NAME_PATTERN = r'id="aliasSpan">(?P<N>.*?)&nbsp;&nbsp;<'
    OFFLINE_PATTERN = r'l10n.(FILES__DOESNT_EXIST|REMOVED)'
    TEMP_OFFLINE_PATTERN = r'l10n.FILES__WARNING'

    UKEY_PATTERN = r"'ukey'\s*:'(\w+)',"
    AB1_PATTERN = r"if\( __ab1 == '(\w+)' \)"
    ERROR_MSG_PATTERN = r'var __error_msg\s*=\s*l10n\.(.*?);'
    LINK_PATTERN = r'"(http://s\d+.filecloud.io/%s/\d+/.*?)"'
    RECAPTCHA_KEY_PATTERN = r"var __recaptcha_public\s*=\s*'([^']+)';"
    RECAPTCHA_KEY = "6Lf5OdISAAAAAEZObLcx5Wlv4daMaASRov1ysDB1"


    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def handleFree(self):
        data = {"ukey": self.file_info['ID']}

        m = re.search(self.AB1_PATTERN, self.html)
        if m is None:
            self.parseError("__AB1")
        data['__ab1'] = m.group(1)

        if not self.account:
            self.fail("User not logged in")
        elif not self.account.logged_in:
            recaptcha = ReCaptcha(self)
            captcha_challenge, captcha_response = recaptcha.challenge(self.RECAPTCHA_KEY)
            self.account.form_data = {"recaptcha_challenge_field": captcha_challenge,
                                      "recaptcha_response_field": captcha_response}
            self.account.relogin(self.user)
            self.retry(2)

        json_url = "http://filecloud.io/download-request.json"
        response = self.load(json_url, post=data)
        self.logDebug(response)
        response = json_loads(response)

        if "error" in response and response['error']:
            self.fail(response)

        self.logDebug(response)
        if response['captcha']:
            recaptcha = ReCaptcha(self)
            m = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
            captcha_key = m.group(1) if m else self.RECAPTCHA_KEY
            data['ctype'] = "recaptcha"

            for _ in xrange(5):
                data['recaptcha_challenge'], data['recaptcha_response'] = recaptcha.challenge(captcha_key)

                json_url = "http://filecloud.io/download-request.json"
                response = self.load(json_url, post=data)
                self.logDebug(response)
                response = json_loads(response)

                if "retry" in response and response['retry']:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
                    break
            else:
                self.fail("Incorrect captcha")

        if response['dl']:
            self.html = self.load('http://filecloud.io/download.html')
            m = re.search(self.LINK_PATTERN % self.file_info['ID'], self.html)
            if m is None:
                self.parseError("Download URL")
            download_url = m.group(1)
            self.logDebug("Download URL: %s" % download_url)

            if "size" in self.file_info and self.file_info['size']:
                self.check_data = {"size": int(self.file_info['size'])}
            self.download(download_url)
        else:
            self.fail("Unexpected server response")

    def handlePremium(self):
        akey = self.account.getAccountData(self.user)['akey']
        ukey = self.file_info['ID']
        self.logDebug("Akey: %s | Ukey: %s" % (akey, ukey))
        rep = self.load("http://api.filecloud.io/api-fetch_download_url.api",
                        post={"akey": akey, "ukey": ukey})
        self.logDebug("FetchDownloadUrl: " + rep)
        rep = json_loads(rep)
        if rep['status'] == 'ok':
            self.download(rep['download_url'], disposition=True)
        else:
            self.fail(rep['message'])


getInfo = create_getInfo(FilecloudIo)
