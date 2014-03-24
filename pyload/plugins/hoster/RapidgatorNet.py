# -*- coding: utf-8 -*-
###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: zoidberg
###############################################################################

import re
from pycurl import HTTPHEADER

from module.common.json_layer import json_loads
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha, SolveMedia, AdsCaptcha


class RapidgatorNet(SimpleHoster):
    __name__ = "RapidgatorNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?(rapidgator\.net|rg\.to)/file/\w+"
    __version__ = "0.21"
    __description__ = """Rapidgator.net hoster plugin"""
    __author_name__ = ("zoidberg", "chrox", "stickell", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "", "l.stickell@yahoo.it", "vuolter@gmail.com")

    API_URL = 'http://rapidgator.net/api/file'

    FILE_NAME_PATTERN = r'<title>Download file (?P<N>.*)</title>'
    FILE_SIZE_PATTERN = r'File size:\s*<strong>(?P<S>[\d\.]+) (?P<U>\w+)</strong>'
    FILE_OFFLINE_PATTERN = r'>(File not found|Error 404)'

    JSVARS_PATTERN = r"\s+var\s*(startTimerUrl|getDownloadUrl|captchaUrl|fid|secs)\s*=\s*'?(.*?)'?;"
    PREMIUM_ONLY_ERROR_PATTERN = r'You can download files up to|This file can be downloaded by premium only<'
    DOWNLOAD_LIMIT_ERROR_PATTERN = r'You have reached your (daily|hourly) downloads limit'
    WAIT_PATTERN = r'(?:Delay between downloads must be not less than|Try again in)\s*(\d+)\s*(hour|min)'
    DOWNLOAD_LINK_PATTERN = r"return '(http://\w+.rapidgator.net/.*)';"

    RECAPTCHA_KEY_PATTERN = r'"http://api\.recaptcha\.net/challenge\?k=(.*?)"'
    ADSCAPTCHA_SRC_PATTERN = r'(http://api\.adscaptcha\.com/Get\.aspx[^"\']*)'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.script\?k=(.*?)"'

    def setup(self):
        self.resumeDownload = self.multiDL = self.premium
        self.sid = None
        self.chunkLimit = 1
        self.req.setOption("timeout", 120)

    def process(self, pyfile):
        if self.account:
            self.sid = self.account.getAccountData(self.user).get('SID', None)

        if self.sid:
            self.handlePremium()
        else:
            self.handleFree()

    def api_response(self, cmd):
        try:
            json = self.load('%s/%s' % (self.API_URL, cmd),
                             get={'sid': self.sid,
                                  'url': self.pyfile.url}, decode=True)
            self.logDebug('API:%s' % cmd, json, "SID: %s" % self.sid)
            json = json_loads(json)
            status = json['response_status']
            msg = json['response_details']
        except BadHeader, e:
            self.logError('API:%s' % cmd, e, "SID: %s" % self.sid)
            status = e.code
            msg = e

        if status == 200:
            return json['response']
        elif status == 423:
            self.account.empty(self.user)
            self.retry()
        else:
            self.account.relogin(self.user)
            self.retry(wait_time=60)

    def handlePremium(self):
        #self.logDebug("ACCOUNT_DATA", self.account.getAccountData(self.user))
        self.api_data = self.api_response('info')
        self.api_data['md5'] = self.api_data['hash']
        self.pyfile.name = self.api_data['filename']
        self.pyfile.size = self.api_data['size']
        url = self.api_response('download')['url']
        self.download(url)

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        self.checkFree()

        jsvars = dict(re.findall(self.JSVARS_PATTERN, self.html))
        self.logDebug(jsvars)

        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        url = "http://rapidgator.net%s?fid=%s" % (
            jsvars.get('startTimerUrl', '/download/AjaxStartTimer'), jsvars["fid"])
        jsvars.update(self.getJsonResponse(url))

        self.wait(int(jsvars.get('secs', 45)) + 1, False)

        url = "http://rapidgator.net%s?sid=%s" % (
            jsvars.get('getDownloadUrl', '/download/AjaxGetDownload'), jsvars["sid"])
        jsvars.update(self.getJsonResponse(url))

        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With:"])

        url = "http://rapidgator.net%s" % jsvars.get('captchaUrl', '/download/captcha')
        self.html = self.load(url)

        for _ in xrange(5):
            found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
            if found:
                link = found.group(1)
                self.logDebug(link)
                self.download(link, disposition=True)
                break
            else:
                captcha, captcha_key = self.getCaptcha()
                captcha_challenge, captcha_response = captcha.challenge(captcha_key)

                self.html = self.load(url, post={
                    "DownloadCaptchaForm[captcha]": "",
                    "adcopy_challenge": captcha_challenge,
                    "adcopy_response": captcha_response
                })

                if "The verification code is incorrect" in self.html:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
        else:
            self.parseError("Download link")

    def getCaptcha(self):
        found = re.search(self.ADSCAPTCHA_SRC_PATTERN, self.html)
        if found:
            captcha_key = found.group(1)
            captcha = AdsCaptcha(self)
        else:
            found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
            if found:
                captcha_key = found.group(1)
                captcha = ReCaptcha(self)
            else:
                found = re.search(self.SOLVEMEDIA_PATTERN, self.html)
                if found:
                    captcha_key = found.group(1)
                    captcha = SolveMedia(self)
                else:
                    self.parseError("Captcha")

        return captcha, captcha_key

    def checkFree(self):
        found = re.search(self.PREMIUM_ONLY_ERROR_PATTERN, self.html)
        if found:
            self.fail("Premium account needed for download")
        else:
            found = re.search(self.WAIT_PATTERN, self.html)

        if found:
            wait_time = int(found.group(1)) * {"hour": 60, "min": 1}[found.group(2)]
        else:
            found = re.search(self.DOWNLOAD_LIMIT_ERROR_PATTERN, self.html)
            if not found:
                return
            elif found.group(1) == "daily":
                wait_time = 60
            else:
                wait_time = 24 * 60

        self.logDebug("Waiting %d minutes" % wait_time)
        self.wait(wait_time * 60, True)
        self.retry()

    def getJsonResponse(self, url):
        response = self.load(url, decode=True)
        if not response.startswith('{'):
            self.retry()
        self.logDebug(url, response)
        return json_loads(response)


getInfo = create_getInfo(RapidgatorNet)
