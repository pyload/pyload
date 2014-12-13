# -*- coding: utf-8 -*-

import re

from random import random
from time import sleep

from pyload.plugin.hoster.UnrestrictLi import secondsToMidnight
from pyload.plugin.internal.captcha import ReCaptcha, SolveMedia
from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo
from pyload.utils import html_unescape


class XFSHoster(SimpleHoster):
    __name    = "XFSHoster"
    __type    = "hoster"
    __version = "0.27"

    __pattern = r'^unmatchable$'

    __description = """XFileSharing hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None
    HOSTER_NAME   = None

    TEXT_ENCODING     = False
    COOKIES           = [(HOSTER_DOMAIN, "lang", "english")]
    CHECK_DIRECT_LINK = None
    MULTI_HOSTER      = True  #@NOTE: Should be default to False for safe, but I'm lazy...

    NAME_PATTERN = r'(>Filename:</b></td><td nowrap>|name="fname" value="|<span class="name">)(?P<N>.+?)(\s*<|")'
    SIZE_PATTERN = r'(>Size:</b></td><td>|>File:.*>|<span class="size">)(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'

    WAIT_PATTERN         = r'<span id="countdown_str">.*?>(\d+)</span>|id="countdown" value=".*?(\d+).*?"'
    PREMIUM_ONLY_PATTERN = r'>This file is available for Premium Users only'
    ERROR_PATTERN        = r'(?:class=["\']err["\'].*?>|<[Cc]enter><b>|>Error</td>|>\(ERROR:)(?:\s*<.+?>\s*)*(.+?)(?:["\']|<|\))'

    LEECH_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    LINK_PATTERN       = None  #: final download url pattern

    CAPTCHA_PATTERN       = r'(https?://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_BLOCK_PATTERN = r'>Enter code.*?<div.*?>(.+?)</div>'
    RECAPTCHA_PATTERN     = None
    SOLVEMEDIA_PATTERN    = None

    FORM_PATTERN    = None
    FORM_INPUTS_MAP = None  #: dict passed as input_names to parseHtmlForm


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

        self.captcha   = None
        self.errmsg    = None
        self.passwords = self.getPassword().splitlines()

        super(XFSHoster, self).prepare()

        if self.CHECK_DIRECT_LINK is None:
            self.directDL = bool(self.premium)


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
        for i in xrange(1, 6):
            self.logDebug("Getting download link: #%d" % i)

            self.checkErrors()

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

            data = self.getPostParameters()

            self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True, follow_location=False)

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m and not "op=" in m.group(1):
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break
        else:
            self.logError(data['op'] if 'op' in data else _("UNKNOWN"))
            return ""

        self.errmsg = None

        return m.group(1)


    def handleMulti(self):
        #only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_DOMAIN)

        action, inputs = self.parseHtmlForm()

        upload_id = "%012d" % int(random() * 10 ** 12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"

        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(action, inputs)

        self.req.setOption("timeout", 600)  #: wait for file to upload to easybytez.com

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
        m = re.search(self.LEECH_LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LEECH_LINK_PATTERN not found"))

        header = self.load(m.group(1), just_header=True, decode=True)

        if 'location' in header:  #: Direct download link
            self.link = header['location']
        else:
            self.fail(_("Download link not found"))


    def checkErrors(self):
        m = re.search(self.PREMIUM_ONLY_PATTERN, self.html)
        if m:
            self.info['error'] = "premium-only"
            return

        m = re.search(self.ERROR_PATTERN, self.html)

        if m is None:
            self.errmsg = None
        else:
            self.errmsg = m.group(1).strip()

            self.logWarning(re.sub(r"<.*?>", " ", self.errmsg))

            if 'wait' in self.errmsg:
                wait_time = sum([int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(hr|hour|min|sec)', self.errmsg, re.I)])
                self.wait(wait_time, True)

            elif 'country' in self.errmsg:
                self.fail(_("Downloads are disabled for your country"))

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
                    retries = 24

                self.wantReconnect = True
                self.retry(retries, delay, _("Download limit exceeded"))

            elif 'countdown' in self.errmsg or 'Expired' in self.errmsg:
                self.retry(reason=_("Link expired"))

            elif 'maintenance' in self.errmsg or 'maintainance' in self.errmsg:
                self.tempOffline()

            elif 'download files up to' in self.errmsg:
                self.fail(_("File too large for free download"))

            else:
                self.wantReconnect = True
                self.retry(wait_time=60, reason=self.errmsg)

        if self.errmsg:
            self.info['error'] = self.errmsg
        else:
            self.info.pop('error', None)


    def getPostParameters(self):
        if self.FORM_PATTERN or self.FORM_INPUTS_MAP:
            action, inputs = self.parseHtmlForm(self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {})
        else:
            action, inputs = self.parseHtmlForm(input_names={'op': re.compile(r'^download')})

        if not inputs:
            action, inputs = self.parseHtmlForm('F1')
            if not inputs:
                if self.errmsg:
                    self.retry(reason=self.errmsg)
                else:
                    self.error(_("TEXTAREA F1 not found"))

        self.logDebug(inputs)

        if 'op' in inputs:
            if "password" in inputs:
                if self.passwords:
                    inputs['password'] = self.passwords.pop(0)
                else:
                    self.fail(_("Missing password"))

            if not self.premium:
                m = re.search(self.WAIT_PATTERN, self.html)
                if m:
                    wait_time = int(m.group(1))
                    self.setWait(wait_time, False)

                self.captcha = self.handleCaptcha(inputs)

                self.wait()
        else:
            inputs['referer'] = self.pyfile.url

        if self.premium:
            inputs['method_premium'] = "Premium Download"
            inputs.pop('method_free', None)
        else:
            inputs['method_free'] = "Free Download"
            inputs.pop('method_premium', None)

        return inputs


    def handleCaptcha(self, inputs):
        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m:
            captcha_url = m.group(1)
            inputs['code'] = self.decryptCaptcha(captcha_url)
            return 1

        m = re.search(self.CAPTCHA_BLOCK_PATTERN, self.html, re.S)
        if m:
            captcha_div = m.group(1)
            numerals    = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))
            self.logDebug(captcha_div)
            inputs['code'] = "".join([a[1] for a in sorted(numerals, key=lambda num: int(num[0]))])
            self.logDebug("Captcha code: %s" % inputs['code'], numerals)
            return 2

        recaptcha = ReCaptcha(self)
        try:
            captcha_key = re.search(self.RECAPTCHA_PATTERN, self.html).group(1)
        except Exception:
            captcha_key = recaptcha.detect_key()
        else:
            self.logDebug("ReCaptcha key: %s" % captcha_key)

        if captcha_key:
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(captcha_key)
            return 3

        solvemedia = SolveMedia(self)
        try:
            captcha_key = re.search(self.SOLVEMEDIA_PATTERN, self.html).group(1)
        except Exception:
            captcha_key = solvemedia.detect_key()
        else:
            self.logDebug("SolveMedia key: %s" % captcha_key)

        if captcha_key:
            inputs['adcopy_challenge'], inputs['adcopy_response'] = solvemedia.challenge(captcha_key)
            return 4

        return 0
