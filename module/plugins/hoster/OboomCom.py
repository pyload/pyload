# -*- coding: utf-8 -*-
#
# Test links:
# https://www.oboom.com/B7CYZIEB/10Mio.dat

import re

from module.common.json_layer import json_loads
from module.plugins.internal.Hoster import Hoster
from module.plugins.captcha.ReCaptcha import ReCaptcha


class OboomCom(Hoster):
    __name__    = "OboomCom"
    __type__    = "hoster"
    __version__ = "0.36"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?oboom\.com/(?:#(?:id=|/)?)?(?P<ID>\w{8})'

    __description__ = """Oboom.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stanley", "stanley.foerster@gmail.com")]


    RECAPTCHA_KEY = "6LdqpO0SAAAAAJGHXo63HyalP7H4qlRs_vff0kJX"


    def setup(self):
        self.chunk_limit = 1
        self.multiDL = self.resume_download = self.premium


    def process(self, pyfile):
        self.pyfile.url.replace(".com/#id=", ".com/#")
        self.pyfile.url.replace(".com/#/", ".com/#")
        self.html = self.load(pyfile.url)
        self.get_file_id(self.pyfile.url)
        self.get_session_token()
        self.get_fileInfo(self.session_token, self.file_id)
        self.pyfile.name = self.file_name
        self.pyfile.size = self.file_size
        if not self.premium:
            self.solve_captcha()
        self.get_download_ticket()
        self.download("http://%s/1.0/dlh" % self.download_domain, get={'ticket': self.download_ticket, 'http_errors': 0})


    def load_url(self, url, get=None):
        if get is None:
            get = {}
        return json_loads(self.load(url, get))


    def get_file_id(self, url):
        self.file_id = re.match(OboomCom.__pattern__, url).group('ID')


    def get_session_token(self):
        if self.premium:
            accountInfo = self.account.get_data(self.user, True)
            if "session" in accountInfo:
                self.session_token = accountInfo['session']
            else:
                self.fail(_("Could not retrieve premium session"))
        else:
            apiUrl = "http://www.oboom.com/1.0/guestsession"
            result = self.load_url(apiUrl)
            if result[0] == 200:
                self.session_token = result[1]
            else:
                self.fail(_("Could not retrieve token for guest session. Error code: %s") % result[0])


    def solve_captcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)
            apiUrl = "http://www.oboom.com/1.0/download/ticket"
            params = {'recaptcha_challenge_field': challenge,
                      'recaptcha_response_field': response,
                      'download_id': self.file_id,
                      'token': self.session_token}
            result = self.load_url(apiUrl, params)

            if result[0] == 200:
                self.download_token = result[1]
                self.download_auth = result[2]
                self.captcha.correct()
                self.wait(30)
                break

            elif result[0] == 400:
                if result[1] == "incorrect-captcha-sol":
                    self.captcha.invalid()
                elif result[1] == "captcha-timeout":
                    self.captcha.invalid()
                elif result[1] == "forbidden":
                    self.retry(5, 15 * 60, _("Service unavailable"))

            elif result[0] == 403:
                if result[1] == -1:  #: Another download is running
                    self.set_wait(15 * 60)
                else:
                    self.set_wait(result[1], True)
                self.wait()
                self.retry(5)
        else:
            self.captcha.invalid()
            self.fail(_("Received invalid captcha 5 times"))


    def get_fileInfo(self, token, fileId):
        apiUrl = "http://api.oboom.com/1.0/info"
        params = {'token': token, 'items': fileId, 'http_errors': 0}

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            item = result[1][0]
            if item['state'] == "online":
                self.file_size = item['size']
                self.file_name = item['name']
            else:
                self.offline()
        else:
            self.fail(_("Could not retrieve file info. Error code %s: %s") % (result[0], result[1]))


    def get_download_ticket(self):
        apiUrl = "http://api.oboom.com/1/dl"
        params = {'item': self.file_id, 'http_errors': 0}
        if self.premium:
            params['token'] = self.session_token
        else:
            params['token'] = self.download_token
            params['auth'] = self.download_auth

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            self.download_domain = result[1]
            self.download_ticket = result[2]
        elif result[0] == 421:
            self.retry(wait_time=result[2] + 60, reason=_("Connection limit exceeded"))
        else:
            self.fail(_("Could not retrieve download ticket. Error code: %s") % result[0])
