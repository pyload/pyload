# -*- coding: utf-8 -*-

import pycurl
import random
import re
import urlparse

from module.plugins.internal.CaptchaService import ReCaptcha, SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, secondsToMidnight
from module.utils import html_unescape


class XFSHoster(SimpleHoster):
    __name__    = "XFSHoster"
    __type__    = "hoster"
    __version__ = "0.50"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharing hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg"      , "zoidberg@mujmail.cz"),
                       ("stickell"      , "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    HOSTER_DOMAIN = None

    TEXT_ENCODING = False
    DIRECT_LINK   = None
    MULTI_HOSTER  = True  #@NOTE: Should be default to False for safe, but I'm lazy...

    NAME_PATTERN = r'(Filename[ ]*:[ ]*</b>(</td><td nowrap>)?|name="fname"[ ]+value="|<[\w^_]+ class="(file)?name">)\s*(?P<N>.+?)(\s*<|")'
    SIZE_PATTERN = r'(Size[ ]*:[ ]*</b>(</td><td>)?|File:.*>|</font>\s*\(|<[\w^_]+ class="size">)\s*(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'

    WAIT_PATTERN         = r'<span id="countdown_str".*>(\d+)</span>|id="countdown" value=".*?(\d+).*?"'
    PREMIUM_ONLY_PATTERN = r'>This file is available for Premium Users only'
    HAPPY_HOUR_PATTERN   = r'>[Hh]appy hour'
    ERROR_PATTERN        = r'(?:class=["\']err["\'].*?>|<[Cc]enter><b>|>Error</td>|>\(ERROR:)(?:\s*<.+?>\s*)*(.+?)(?:["\']|<|\))'

    LINK_LEECH_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    LINK_PATTERN       = None  #: final download url pattern

    CAPTCHA_PATTERN       = r'(https?://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_BLOCK_PATTERN = r'>Enter code.*?<div.*?>(.+?)</div>'
    RECAPTCHA_PATTERN     = None
    SOLVEMEDIA_PATTERN    = None

    FORM_PATTERN    = None
    FORM_INPUTS_MAP = None  #: dict passed as input_names to parseHtmlForm


    def setup(self):
        self.chunkLimit     = -1 if self.premium else 1
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        """ Initialize important variables """
        if not self.HOSTER_DOMAIN:
            if self.account:
                account = self.account
            else:
                account = self.pyfile.m.core.accountManager.getAccountPlugin(self.__name__)

            if account and hasattr(account, "HOSTER_DOMAIN") and account.HOSTER_DOMAIN:
                self.HOSTER_DOMAIN = account.HOSTER_DOMAIN
            else:
                self.fail(_("Missing HOSTER_DOMAIN"))

        if isinstance(self.COOKIES, list):
            self.COOKIES.insert((self.HOSTER_DOMAIN, "lang", "english"))

        if not self.LINK_PATTERN:
            pattern = r'(https?://(?:www\.)?([^/]*?%s|\d+\.\d+\.\d+\.\d+)(\:\d+)?(/d/|(/files)?/\d+/\w+/).+?)["\'<]'
            self.LINK_PATTERN = pattern % self.HOSTER_DOMAIN.replace('.', '\.')

        super(XFSHoster, self).prepare()

        if self.DIRECT_LINK is None:
            self.directDL = self.premium


    def handleFree(self, pyfile):
        for i in xrange(1, 6):
            self.logDebug("Getting download link: #%d" % i)

            self.checkErrors()

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

            data = self.getPostParameters()

            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)

            self.html = self.load(pyfile.url, post=data, decode=True)

            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m and not "op=" in m.group(1):
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break
        else:
            self.logError(data['op'] if 'op' in data else _("UNKNOWN"))
            return ""

        self.link = m.group(1).strip()  #@TODO: Remove .strip() in 0.4.10


    def handlePremium(self, pyfile):
        return self.handleFree(pyfile)


    def handleMulti(self, pyfile):
        if not self.account:
            self.fail(_("Only registered or premium users can use url leech feature"))

        #only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_DOMAIN)

        action, inputs = self.parseHtmlForm()

        upload_id = "%012d" % int(random.random() * 10 ** 12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"

        inputs['tos'] = '1'
        inputs['url_mass'] = pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(action, inputs)

        self.req.setOption("timeout", 600)  #: wait for file to upload to easybytez.com

        self.html = self.load(action, post=inputs)

        self.checkErrors()

        action, inputs = self.parseHtmlForm('F1')
        if not inputs:
            self.retry(reason=self.info['error'] if 'error' in self.info else _("TEXTAREA F1 not found"))

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
        m = re.search(self.LINK_LEECH_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_LEECH_PATTERN not found"))

        header = self.load(m.group(1), just_header=True, decode=True)

        if 'location' in header:  #: Direct download link
            self.link = header['location']


    def getPostParameters(self):
        if self.FORM_PATTERN or self.FORM_INPUTS_MAP:
            action, inputs = self.parseHtmlForm(self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {})
        else:
            action, inputs = self.parseHtmlForm(input_names={'op': re.compile(r'^download')})

        if not inputs:
            action, inputs = self.parseHtmlForm('F1')
            if not inputs:
                self.retry(reason=self.info['error'] if 'error' in self.info else _("TEXTAREA F1 not found"))

        self.logDebug(inputs)

        if 'op' in inputs:
            if "password" in inputs:
                password = self.getPassword()
                if password:
                    inputs['password'] = password
                else:
                    self.fail(_("Missing password"))

            if not self.premium:
                m = re.search(self.WAIT_PATTERN, self.html)
                if m:
                    wait_time = int(m.group(1))
                    self.setWait(wait_time, False)

                self.handleCaptcha(inputs)
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
            return

        m = re.search(self.CAPTCHA_BLOCK_PATTERN, self.html, re.S)
        if m:
            captcha_div = m.group(1)
            numerals    = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))

            self.logDebug(captcha_div)

            inputs['code'] = "".join(a[1] for a in sorted(numerals, key=lambda num: int(num[0])))

            self.logDebug("Captcha code: %s" % inputs['code'], numerals)
            return

        recaptcha = ReCaptcha(self)
        try:
            captcha_key = re.search(self.RECAPTCHA_PATTERN, self.html).group(1)

        except Exception:
            captcha_key = recaptcha.detect_key()

        else:
            self.logDebug("ReCaptcha key: %s" % captcha_key)

        if captcha_key:
            inputs['recaptcha_response_field'], inputs['recaptcha_challenge_field'] = recaptcha.challenge(captcha_key)
            return

        solvemedia = SolveMedia(self)
        try:
            captcha_key = re.search(self.SOLVEMEDIA_PATTERN, self.html).group(1)

        except Exception:
            captcha_key = solvemedia.detect_key()

        else:
            self.logDebug("SolveMedia key: %s" % captcha_key)

        if captcha_key:
            inputs['adcopy_response'], inputs['adcopy_challenge'] = solvemedia.challenge(captcha_key)
