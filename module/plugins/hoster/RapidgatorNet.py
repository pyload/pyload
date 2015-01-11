# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from module.common.json_layer import json_loads
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.CaptchaService import AdsCaptcha, ReCaptcha, SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, secondsToMidnight


class RapidgatorNet(SimpleHoster):
    __name__    = "RapidgatorNet"
    __type__    = "hoster"
    __version__ = "0.29"

    __pattern__ = r'http://(?:www\.)?(rapidgator\.net|rg\.to)/file/\w+'

    __description__ = """Rapidgator.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("chrox", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL = "http://rapidgator.net/api/file"

    COOKIES = [("rapidgator.net", "lang", "en")]

    NAME_PATTERN = r'<title>Download file (?P<N>.*)</title>'
    SIZE_PATTERN = r'File size:\s*<strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong>'
    OFFLINE_PATTERN = r'>(File not found|Error 404)'

    JSVARS_PATTERN = r'\s+var\s*(startTimerUrl|getDownloadUrl|captchaUrl|fid|secs)\s*=\s*\'?(.*?)\'?;'
    PREMIUM_ONLY_ERROR_PATTERN = r'You can download files up to|This file can be downloaded by premium only<'
    DOWNLOAD_LIMIT_ERROR_PATTERN = r'You have reached your (daily|hourly) downloads limit'
    WAIT_PATTERN = r'(?:Delay between downloads must be not less than|Try again in)\s*(\d+)\s*(hour|min)'
    LINK_FREE_PATTERN = r'return \'(http://\w+.rapidgator.net/.*)\';'

    RECAPTCHA_PATTERN = r'"http://api\.recaptcha\.net/challenge\?k=(.*?)"'
    ADSCAPTCHA_PATTERN = r'(http://api\.adscaptcha\.com/Get\.aspx[^"\']*)'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.script\?k=(.*?)"'


    def setup(self):
        if self.account:
            self.sid = self.account.getAccountInfo(self.user).get('SID', None)
        else:
            self.sid = None

        if self.sid:
            self.premium = True

        self.resumeDownload = self.multiDL = self.premium
        self.chunkLimit     = 1


    def api_response(self, cmd):
        try:
            json = self.load('%s/%s' % (self.API_URL, cmd),
                             get={'sid': self.sid,
                                  'url': self.pyfile.url}, decode=True)
            self.logDebug("API:%s" % cmd, json, "SID: %s" % self.sid)
            json = json_loads(json)
            status = json['response_status']
            msg = json['response_details']

        except BadHeader, e:
            self.logError("API: %s" % cmd, e, "SID: %s" % self.sid)
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


    def handlePremium(self, pyfile):
        self.api_data = self.api_response('info')
        self.api_data['md5'] = self.api_data['hash']

        pyfile.name = self.api_data['filename']
        pyfile.size = self.api_data['size']

        self.link = self.api_response('download')['url']


    def handleFree(self, pyfile):
        self.checkFree()

        jsvars = dict(re.findall(self.JSVARS_PATTERN, self.html))
        self.logDebug(jsvars)

        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        url = "http://rapidgator.net%s?fid=%s" % (
            jsvars.get('startTimerUrl', '/download/AjaxStartTimer'), jsvars['fid'])
        jsvars.update(self.getJsonResponse(url))

        self.wait(int(jsvars.get('secs', 45)), False)

        url = "http://rapidgator.net%s?sid=%s" % (
            jsvars.get('getDownloadUrl', '/download/AjaxGetDownload'), jsvars['sid'])
        jsvars.update(self.getJsonResponse(url))

        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With:"])

        url = "http://rapidgator.net%s" % jsvars.get('captchaUrl', '/download/captcha')
        self.html = self.load(url)

        for _i in xrange(5):
            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m:
                link = m.group(1)
                self.logDebug(link)
                self.download(link, disposition=True)
                break
            else:
                captcha, captcha_key = self.getCaptcha()
                challenge, response  = captcha.challenge(captcha_key)

                self.html = self.load(url, post={'DownloadCaptchaForm[captcha]': "",
                                                 'adcopy_challenge'            : challenge,
                                                 'adcopy_response'             : response})

                if "The verification code is incorrect" in self.html:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
        else:
            self.error(_("Download link"))


    def getCaptcha(self):
        m = re.search(self.ADSCAPTCHA_PATTERN, self.html)
        if m:
            captcha_key = m.group(1)
            captcha = AdsCaptcha(self)
        else:
            m = re.search(self.RECAPTCHA_PATTERN, self.html)
            if m:
                captcha_key = m.group(1)
                captcha = ReCaptcha(self)
            else:
                m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
                if m:
                    captcha_key = m.group(1)
                    captcha = SolveMedia(self)
                else:
                    self.error(_("Captcha"))

        return captcha, captcha_key


    def checkFree(self):
        m = re.search(self.PREMIUM_ONLY_ERROR_PATTERN, self.html)
        if m:
            self.fail(_("Premium account needed for download"))
        else:
            m = re.search(self.WAIT_PATTERN, self.html)

        if m:
            wait_time = int(m.group(1)) * {"hour": 60, "min": 1}[m.group(2)]
        else:
            m = re.search(self.DOWNLOAD_LIMIT_ERROR_PATTERN, self.html)
            if m is None:
                return
            elif m.group(1) == "daily":
                self.logWarning(_("You have reached your daily downloads limit for today"))
                wait_time = secondsToMidnight(gmt=2)
            else:
                wait_time = 1 * 60 * 60

        self.logDebug("Waiting %d minutes" % wait_time / 60)
        self.wait(wait_time, True)
        self.retry()


    def getJsonResponse(self, url):
        res = self.load(url, decode=True)
        if not res.startswith('{'):
            self.retry()
        self.logDebug(url, res)
        return json_loads(res)


getInfo = create_getInfo(RapidgatorNet)
