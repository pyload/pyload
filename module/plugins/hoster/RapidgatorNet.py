# -*- coding: utf-8 -*-

import pycurl
import re

from module.common.json_layer import json_loads
from module.network.HTTPRequest import BadHeader
from module.plugins.captcha.AdsCaptcha import AdsCaptcha
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.captcha.SolveMedia import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RapidgatorNet(SimpleHoster):
    __name__    = "RapidgatorNet"
    __type__    = "hoster"
    __version__ = "0.35"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(rapidgator\.net|rg\.to)/file/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Rapidgator.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("chrox", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL = "http://rapidgator.net/api/file"

    COOKIES = [("rapidgator.net", "lang", "en")]

    NAME_PATTERN    = r'<title>Download file (?P<N>.*)</title>'
    SIZE_PATTERN    = r'File size:\s*<strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong>'
    OFFLINE_PATTERN = r'>(File not found|Error 404)'

    JSVARS_PATTERN = r'\s+var\s*(startTimerUrl|getDownloadUrl|captchaUrl|fid|secs)\s*=\s*\'?(.*?)\'?;'

    PREMIUM_ONLY_PATTERN = r'You can download files up to|This file can be downloaded by premium only<'
    ERROR_PATTERN        = r'You have reached your (?:daily|hourly) downloads limit'
    WAIT_PATTERN         = r'(Delay between downloads must be not less than|Try again in).+'

    LINK_FREE_PATTERN = r'return \'(http://\w+.rapidgator.net/.*)\';'

    RECAPTCHA_PATTERN  = r'"http://api\.recaptcha\.net/challenge\?k=(.*?)"'
    ADSCAPTCHA_PATTERN = r'(http://api\.adscaptcha\.com/Get\.aspx[^"\']+)'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.script\?k=(.*?)"'


    def setup(self):
        if self.account:
            self.sid = self.account.get_data(self.user).get('sid', None)
        else:
            self.sid = None

        if self.sid:
            self.premium = True

        self.resume_download = self.multiDL = self.premium
        self.chunk_limit     = 1


    def api_response(self, cmd):
        try:
            json = self.load('%s/%s' % (self.API_URL, cmd),
                             get={'sid': self.sid,
                                  'url': self.pyfile.url})
            self.log_debug("API:%s" % cmd, json, "SID: %s" % self.sid)
            json = json_loads(json)
            status = json['response_status']
            msg = json['response_details']

        except BadHeader, e:
            self.log_error("API: %s" % cmd, e, "SID: %s" % self.sid)
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


    def handle_premium(self, pyfile):
        self.api_data = self.api_response('info')
        self.api_data['md5'] = self.api_data['hash']

        pyfile.name = self.api_data['filename']
        pyfile.size = self.api_data['size']

        self.link = self.api_response('download')['url']


    def handle_free(self, pyfile):
        jsvars = dict(re.findall(self.JSVARS_PATTERN, self.html))
        self.log_debug(jsvars)

        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        url = "http://rapidgator.net%s?fid=%s" % (
            jsvars.get('startTimerUrl', '/download/AjaxStartTimer'), jsvars['fid'])
        jsvars.update(self.get_json_response(url))

        self.wait(jsvars.get('secs', 45), False)

        url = "http://rapidgator.net%s?sid=%s" % (
            jsvars.get('getDownloadUrl', '/download/AjaxGetDownload'), jsvars['sid'])
        jsvars.update(self.get_json_response(url))

        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        url = "http://rapidgator.net%s" % jsvars.get('captchaUrl', '/download/captcha')
        self.html = self.load(url)

        for _i in xrange(5):
            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m:
                self.link = m.group(1)
                break
            else:
                captcha = self.handle_captcha()

                if not captcha:
                    self.error(_("Captcha pattern not found"))

                response, challenge  = captcha.challenge()

                self.html = self.load(url, post={'DownloadCaptchaForm[captcha]': "",
                                                 'adcopy_challenge'            : challenge,
                                                 'adcopy_response'             : response})

                if "The verification code is incorrect" in self.html:
                    self.captcha.invalid()
                else:
                    self.captcha.correct()
        else:
            self.error(_("Download link"))


    def handle_captcha(self):
        for klass in (AdsCaptcha, ReCaptcha, SolveMedia):
            inst = klass(self)
            if inst.detect_key():
                return inst


    def get_json_response(self, url):
        res = self.load(url)
        if not res.startswith('{'):
            self.retry()
        self.log_debug(url, res)
        return json_loads(res)


getInfo = create_getInfo(RapidgatorNet)
