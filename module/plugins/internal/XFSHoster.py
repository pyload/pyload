# -*- coding: utf-8 -*-

import re

from random import random
from time import sleep

from pycurl import FOLLOWLOCATION, LOW_SPEED_TIME

from module.plugins.hoster.UnrestrictLi import secondsToMidnight
from module.plugins.internal.CaptchaService import ReCaptcha, SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import html_unescape


class XFSHoster(SimpleHoster):
    __name__    = "XFSHoster"
    __type__    = "hoster"
    __version__ = "0.15"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharing hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None
    HOSTER_NAME   = None

    URL_REPLACEMENTS = [(r'/(?:embed-)?(\w{12}).*', r'/\1')]  #: plus support embedded files

    COOKIES = [(HOSTER_DOMAIN, "lang", "english")]

    INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'
    NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    SIZE_PATTERN = r'You have requested .*\((?P<S>[\d.,]+) ?(?P<U>[\w^_]+)?\)</font>'

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'

    WAIT_PATTERN = r'<span id="countdown_str">.*?>(\d+)</span>'

    OVR_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    LINK_PATTERN     = None  #: final download url pattern

    CAPTCHA_PATTERN     = r'(http://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_DIV_PATTERN = r'>Enter code.*?<div.*?>(.+?)</div>'
    RECAPTCHA_PATTERN   = None
    SOLVEMEDIA_PATTERN  = None

    ERROR_PATTERN = r'(?:class=["\']err["\'][^>]*>|<[Cc]enter><b>)(.+?)(?:["\']|</)|>\(ERROR:(.+?)\)'


    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        """ Initialize important variables """
        if not self.HOSTER_DOMAIN:
            self.fail(_("Missing HOSTER_DOMAIN"))

        if not self.HOSTER_NAME:
            self.HOSTER_NAME = "".join([str.capitalize() for str in self.HOSTER_DOMAIN.split('.')])

        if not self.LINK_PATTERN:
            pattern = r'(https?://(www\.)?([^/]*?%s|\d+\.\d+\.\d+\.\d+)(\:\d+)?(/d/|(/files)?/\d+/\w+/).+?)["\'<]'
            self.LINK_PATTERN = pattern % self.HOSTER_DOMAIN.replace('.', '\.')

        self.captcha = None
        self.errmsg = None
        self.passwords = self.getPassword().splitlines()

        if (self.__pattern__ != self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
            and re.match(self.__pattern__, self.pyfile.url) is None):
            self.logInfo(_("Multi hoster detected"))
            if self.premium:
                self.logDebug(_("Looking for download link..."))
                self.handleOverriden()
            else:
                self.fail(_("Only premium users can use url leech feature"))

        return super(XFSHoster, self).prepare()


    def handleFree(self):
        link = self.getDownloadLink()

        if link:
            if self.captcha:
                self.correctCaptcha()

            self.download(link, ref=True, cookies=True, disposition=True)

        elif self.errmsg:
            if 'captcha' in self.errmsg:
                self.fail(_("No valid captcha code entered"))
            else:
                self.fail(self.errmsg)

        else:
            self.fail(_("Download link not found"))


    def handlePremium(self):
        return self.handleFree()


    def getDownloadLink(self):
        for i in xrange(1, 5):
            self.logDebug("Getting download link: #%d" % i)

            self.checkErrors()

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

            data = self.getPostParameters()

            # sleep(10)

            self.req.http.c.setopt(FOLLOWLOCATION, 0)

            self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)
            self.header = self.req.http.header

            self.req.http.c.setopt(FOLLOWLOCATION, 1)

            m = re.search(r'Location\s*:\s*(.+)', self.header, re.I)
            if m:
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break
        else:
            return

        self.errmsg = None

        return m.group(1).strip()  #@TODO: Remove .strip() in 0.4.10


    def handleOverriden(self):
        #only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_DOMAIN)

        action, inputs = self.parseHtmlForm('')

        upload_id = "%012d" % int(random() * 10 ** 12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"

        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(action, inputs)

        self.req.http.c.setopt(LOW_SPEED_TIME, 600)  #: wait for file to upload to easybytez.com

        self.html = self.load(action, post=inputs)

        self.checkErrors()

        action, inputs = self.parseHtmlForm('F1')
        if not inputs:
            if self.errmsg:
                self.retry(reason=self.errmsg)
            else:
                self.error(_("TEXTAREA F1 not found"))

        self.logDebug(inputs)

        stmsg = inputs['st']

        if stmsg == 'OK':
            self.html = self.load(action, post=inputs)

        elif 'Can not leech file' in stmsg:
            self.retry(20, 3 * 60, _("Can not leech file"))

        elif 'today' in stmsg:
            self.retry(wait_time=secondsToMidnight(gmt=2), reason=_("You've used all Leech traffic today"))

        else:
            self.fail(stmsg)

        #get easybytez.com link for uploaded file
        m = re.search(self.OVR_LINK_PATTERN, self.html)
        if m is None:
            self.error(_("OVR_LINK_PATTERN not found"))

        header = self.load(m.group(1).strip(), just_header=True, decode=True)  #@TODO: Remove .strip() in 0.4.10
        if 'location' in header:  #: Direct download link
            self.download(header['location'], ref=True, cookies=True, disposition=True)
        else:
            self.fail(_("Download link not found"))


    def checkErrors(self):
        m = re.search(self.ERROR_PATTERN, self.html)

        if m is None:
            self.errmsg = None
        else:
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
                if 'days' in self.errmsg:
                    delay = secondsToMidnight(gmt=2)
                    retries = 3
                else:
                    delay = 1 * 60 * 60
                    retries = 25

                self.wait(delay, True)
                self.retry(retries, reason=_("Download limit exceeded"))

            elif 'countdown' in self.errmsg or 'Expired' in self.errmsg:
                self.retry(reason=_("Link expired"))

            elif 'maintenance' in self.errmsg or 'maintainance' in self.errmsg:
                self.tempOffline()

            elif 'download files up to' in self.errmsg:
                self.fail(_("File too large for free download"))

            else:
                self.retry(wait_time=60, reason=self.errmsg)

        return self.errmsg


    def getPostParameters(self):
        for _i in xrange(3):
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
                        self.error(_("TEXTAREA F1 not found"))

            self.logDebug(inputs)

            if 'op' in inputs and inputs['op'] in ("download2", "download3"):
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail(_("No or invalid passport"))

                if not self.premium:
                    m = re.search(self.WAIT_PATTERN, self.html)
                    if m:
                        wait_time = int(m.group(1))
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0

                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time:
                        self.wait()

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
            self.logDebug("Captcha code: %s" % inputs['code'], numerals)
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
