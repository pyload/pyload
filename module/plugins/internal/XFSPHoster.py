# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION, LOW_SPEED_TIME
from random import random
from urllib import unquote
from urlparse import urlparse

from module.network.RequestFactory import getURL
from module.plugins.internal.CaptchaService import ReCaptcha, SolveMedia
from module.plugins.internal.SimpleHoster import create_getInfo, replace_patterns, set_cookies, SimpleHoster
from module.plugins.Plugin import Fail
from module.utils import html_unescape


class XFSPHoster(SimpleHoster):
    __name__    = "XFSPHoster"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = None

    __description__ = """XFileSharingPro hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = None

    FILE_URL_REPLACEMENTS = []

    COOKIES = [(HOSTER_NAME, "lang", "english")]

    FILE_INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'
    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested .*\((?P<S>[\d\.\,]+) ?(?P<U>[\w^_]+)?\)</font>'

    OFFLINE_PATTERN = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'

    WAIT_PATTERN = r'<span id="countdown_str">.*?>(\d+)</span>'

    OVR_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    LINK_PATTERN = None  #: final download url pattern

    CAPTCHA_PATTERN = r'(http://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_DIV_PATTERN = r'>Enter code.*?<div.*?>(.+?)</div>'
    RECAPTCHA_PATTERN = None
    SOLVEMEDIA_PATTERN = None

    ERROR_PATTERN = r'(?:class=["\']err["\'][^>]*>|<[Cc]enter><b>)(.+?)(?:["\']|</)'


    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        """ Initialize important variables """
        if not self.HOSTER_NAME:
            self.fail(_("Missing HOSTER_NAME"))

        if not self.LINK_PATTERN:
            pattern = r'(https?://(www\.)?([^/]*?%s|\d+\.\d+\.\d+\.\d+)(\:\d+)?(/d/|(/files)?/\d+/\w+/).+?)["\'<]'
            self.LINK_PATTERN = pattern % self.HOSTER_NAME

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        self.captcha = None
        self.errmsg = None
        self.passwords = self.getPassword().splitlines()

        url = self.pyfile.url = replace_patterns(self.pyfile.url, self.FILE_URL_REPLACEMENTS)
        self.html = getURL(url, decode=not self.TEXT_ENCODING, cookies=bool(self.COOKIES))


    def process(self, pyfile):
        self.prepare()

        if not re.match(self.__pattern__, pyfile.url):
            if self.premium:
                self.handleOverriden()
            else:
                self.fail(_("Only premium users can download from other hosters with %s") % self.HOSTER_NAME)
        else:
            try:
                self.file_info = self.getFileInfo()
            except Fail:
                self.file_info = None

            self.location = self.getDirectDownloadLink()

            if not self.file_info:
                pyfile.name = html_unescape(unquote(urlparse(
                    self.location if self.location else pyfile.url).path.split("/")[-1]))

            if self.location:
                self.startDownload(self.location)
            elif self.premium:
                self.logDebug("Handle as premium download")
                self.handlePremium()
            else:
                self.logDebug("Handle as free download")
                self.handleFree()


    def getDirectDownloadLink(self):
        """ Get download link for premium users with direct download enabled """
        self.req.http.lastURL = self.pyfile.url

        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        self.html = self.load(self.pyfile.url, decode=True)
        self.header = self.req.http.header
        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        location = None
        m = re.search(r"Location\s*:\s*(.*)", self.header, re.I)
        if m and re.match(self.LINK_PATTERN, m.group(1)):
            location = m.group(1).strip()

        return location


    def handleFree(self):
        url = self.getDownloadLink()
        self.startDownload(url)


    def getDownloadLink(self):
        for i in xrange(5):
            self.logDebug("Getting download link: #%d" % i)
            data = self.getPostParameters()

            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)
            self.header = self.req.http.header
            self.req.http.c.setopt(FOLLOWLOCATION, 1)

            m = re.search(r"Location\s*:\s*(.*)", self.header, re.I)
            if m:
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

        else:
            if self.errmsg and 'captcha' in self.errmsg:
                self.fail(_("No valid captcha code entered"))
            else:
                self.fail(_("Download link not found"))

        return m.group(1)


    def handlePremium(self):
        self.html = self.load(self.pyfile.url, post=self.getPostParameters())
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))
        self.startDownload(m.group(1))


    def handleOverriden(self):
        #only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_NAME)
        action, inputs = self.parseHtmlForm('')
        upload_id = "%012d" % int(random() * 10 ** 12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(self.HOSTER_NAME, action, inputs)
        #wait for file to upload to easybytez.com
        self.req.http.c.setopt(LOW_SPEED_TIME, 600)
        self.html = self.load(action, post=inputs)

        action, inputs = self.parseHtmlForm('F1')
        if not inputs:
            self.error(_("TEXTAREA not found"))
        self.logDebug(self.HOSTER_NAME, inputs)
        if inputs['st'] == 'OK':
            self.html = self.load(action, post=inputs)
        elif inputs['st'] == 'Can not leech file':
            self.retry(20, 3 * 60, inputs['st'])
        else:
            self.fail(_(inputs['st']))

        #get easybytez.com link for uploaded file
        m = re.search(self.OVR_LINK_PATTERN, self.html)
        if m is None:
            self.error(_("OVR_LINK_PATTERN not found"))

        self.pyfile.url = m.group(1)

        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:  # Direct link
            self.startDownload(header['location'])
        else:
            self.retry(reason=_("OVR link location not found"))


    def startDownload(self, link):
        link = link.strip()
        if self.captcha:
            self.correctCaptcha()
        self.logDebug("DIRECT LINK: %s" % link)
        self.download(link, disposition=True)


    def checkErrors(self):
        m = re.search(self.ERROR_PATTERN, self.html)
        if m:
            self.errmsg = m.group(1)
            self.logWarning(re.sub(r"<.*?>", " ", self.errmsg))

            if 'wait' in self.errmsg:
                wait_time = sum([int(v) * {"hour": 3600, "minute": 60, "second": 1}[u] for v, u in
                                 re.findall(r'(\d+)\s*(hour|minute|second)', self.errmsg)])
                self.wait(wait_time, True)
            elif 'captcha' in self.errmsg:
                self.invalidCaptcha()
            elif 'premium' in self.errmsg and 'require' in self.errmsg:
                self.fail(_("File can be downloaded by premium users only"))
            elif 'limit' in self.errmsg:
                self.wantReconnect = True
                self.retry(25, 1 * 60 * 60, "Download limit exceeded")
            elif 'countdown' in self.errmsg or 'Expired' in self.errmsg:
                self.retry(reason=_("Link expired"))
            elif 'maintenance' in self.errmsg or 'maintainance' in self.errmsg:
                self.tempOffline()
            elif 'download files up to' in self.errmsg:
                self.fail(_("File too large for free download"))
            else:
                self.fail(self.errmsg)

        else:
            self.errmsg = None

        return self.errmsg


    def getPostParameters(self):
        for _i in xrange(3):
            self.checkErrors()

            if hasattr(self, "FORM_PATTERN"):
                action, inputs = self.parseHtmlForm(self.FORM_PATTERN)
            else:
                action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})

            if not inputs:
                action, inputs = self.parseHtmlForm('F1')
                if not inputs:
                    if self.errmsg:
                        self.retry(reason=self.errmsg)
                    else:
                        self.error(_("Form not found"))

            self.logDebug(self.HOSTER_NAME, inputs)

            if 'op' in inputs and inputs['op'] in ("download2", "download3"):
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail(_("No or invalid passport"))

                if not self.premium:
                    m = re.search(self.WAIT_PATTERN, self.html)
                    if m:
                        wait_time = int(m.group(1)) + 1
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0

                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time:
                        self.wait()

                self.errmsg = None
                return inputs

            else:
                inputs['referer'] = self.pyfile.url

                if self.premium:
                    inputs['method_premium'] = "Premium Download"
                    if 'method_free' in inputs:
                        del inputs['method_free']
                else:
                    inputs['method_free'] = "Free Download"
                    if 'method_premium' in inputs:
                        del inputs['method_premium']

                self.html = self.load(self.pyfile.url, post=inputs, ref=True)
                self.errmsg = None

        else:
            self.error(_("FORM: %s") % (inputs['op'] if 'op' in inputs else _("UNKNOWN")))


    def handleCaptcha(self, inputs):
        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m:
            captcha_url = m.group(1)
            inputs['code'] = self.decryptCaptcha(captcha_url)
            return 1

        m = re.search(self.CAPTCHA_DIV_PATTERN, self.html, re.S)
        if m:
            captcha_div = m.group(1)
            self.logDebug(captcha_div)
            numerals = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))
            inputs['code'] = "".join([a[1] for a in sorted(numerals, key=lambda num: int(num[0]))])
            self.logDebug("CAPTCHA", inputs['code'], numerals)
            return 2

        recaptcha = ReCaptcha(self)
        try:
            captcha_key = re.search(self.RECAPTCHA_PATTERN, self.html).group(1)
        except:
            captcha_key = recaptcha.detect_key()

        if captcha_key:
            self.logDebug("ReCaptcha key: %s" % captcha_key)
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(captcha_key)
            return 3

        solvemedia = SolveMedia(self)
        try:
            captcha_key = re.search(self.SOLVEMEDIA_PATTERN, self.html).group(1)
        except:
            captcha_key = solvemedia.detect_key()

        if captcha_key:
            self.logDebug("SolveMedia key: %s" % captcha_key)
            inputs['adcopy_challenge'], inputs['adcopy_response'] = solvemedia.challenge(captcha_key)
            return 4

        return 0
