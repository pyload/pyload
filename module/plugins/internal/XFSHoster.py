# -*- coding: utf-8 -*-

import pycurl
import random
import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.captcha.SolveMedia import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, seconds_to_midnight
from module.utils import html_unescape


class XFSHoster(SimpleHoster):
    __name__    = "XFSHoster"
    __type__    = "hoster"
    __version__ = "0.55"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharing hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg"      , "zoidberg@mujmail.cz"),
                       ("stickell"      , "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    HOSTER_DOMAIN = None

    LEECH_HOSTER = True  #@NOTE: Should be default to False for safe, but I'm lazy...

    NAME_PATTERN = r'(Filename[ ]*:[ ]*</b>(</td><td nowrap>)?|name="fname"[ ]+value="|<[\w^_]+ class="(file)?name">)\s*(?P<N>.+?)(\s*<|")'
    SIZE_PATTERN = r'(Size[ ]*:[ ]*</b>(</td><td>)?|File:.*>|</font>\s*\(|<[\w^_]+ class="size">)\s*(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed|no longer available)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'

    WAIT_PATTERN         = r'<span id="countdown_str".*>(\d+)</span>|id="countdown" value=".*?(\d+).*?"'
    PREMIUM_ONLY_PATTERN = r'>This file is available for Premium Users only'
    HAPPY_HOUR_PATTERN   = r'>[Hh]appy hour'
    ERROR_PATTERN        = r'(?:class=["\']err["\'].*?>|<[Cc]enter><b>|>Error</td>|>\(ERROR:)(?:\s*<.+?>\s*)*(.+?)(?:["\']|<|\))'

    LINK_LEECH_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'

    CAPTCHA_PATTERN       = r'(https?://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_BLOCK_PATTERN = r'>Enter code.*?<div.*?>(.+?)</div>'
    RECAPTCHA_PATTERN     = None
    SOLVEMEDIA_PATTERN    = None

    FORM_PATTERN    = None
    FORM_INPUTS_MAP = None  #: Dict passed as input_names to parse_html_form


    def setup(self):
        self.chunk_limit     = -1 if self.premium else 1
        self.resume_download = self.multiDL = self.premium


    def prepare(self):
        """
        Initialize important variables
        """
        if not self.HOSTER_DOMAIN:
            if self.account:
                account = self.account
            else:
                account = self.pyload.accountManager.getAccountPlugin(self.__name__)

            if account and hasattr(account, "HOSTER_DOMAIN") and account.HOSTER_DOMAIN:
                self.HOSTER_DOMAIN = account.HOSTER_DOMAIN
            else:
                self.fail(_("Missing HOSTER_DOMAIN"))

        if isinstance(self.COOKIES, list):
            self.COOKIES.insert((self.HOSTER_DOMAIN, "lang", "english"))

        if not self.LINK_PATTERN:
            pattern = r'(?:file: "(.+?)"|(https?://(?:www\.)?([^/]*?%s|\d+\.\d+\.\d+\.\d+)(\:\d+)?(/d/|(/files)?/\d+/\w+/).+?)["\'<])'
            self.LINK_PATTERN = pattern % self.HOSTER_DOMAIN.replace('.', '\.')

        super(XFSHoster, self).prepare()

        if self.DIRECT_LINK is None:
            self.direct_dl = self.premium


    def handle_free(self, pyfile):
        for i in xrange(1, 6):
            self.log_debug("Getting download link #%d" % i)

            self.check_errors()

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

            data = self.get_post_parameters()

            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)

            self.html = self.load(pyfile.url, post=data)

            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m and not "op=" in m.group(1):
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break
        else:
            if 'op' in data:
                self.error(_("Missing OP data after: ") + data['op'])

        self.link = m.group(1)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


    def handle_multi(self, pyfile):
        if not self.account:
            self.fail(_("Only registered or premium users can use url leech feature"))

        #: Only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_DOMAIN)

        action, inputs = self.parse_html_form()

        upload_id = "%012d" % int(random.random() * 10 ** 12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"

        inputs['tos'] = '1'
        inputs['url_mass'] = pyfile.url
        inputs['up1oad_type'] = 'url'

        self.log_debug(action, inputs)

        self.req.setOption("timeout", 600)  #: Wait for file to upload to easybytez.com

        self.html = self.load(action, post=inputs)

        self.check_errors()

        action, inputs = self.parse_html_form('F1')
        if not inputs:
            self.retry(reason=self.info['error'] if 'error' in self.info else _("TEXTAREA F1 not found"))

        self.log_debug(inputs)

        stmsg = inputs['st']

        if stmsg == 'OK':
            self.html = self.load(action, post=inputs)

        elif 'Can not leech file' in stmsg:
            self.retry(20, 3 * 60, _("Can not leech file"))

        elif 'today' in stmsg:
            self.retry(wait_time=seconds_to_midnight(gmt=2), reason=_("You've used all Leech traffic today"))

        else:
            self.fail(stmsg)

        #: Get easybytez.com link for uploaded file
        m = re.search(self.LINK_LEECH_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_LEECH_PATTERN not found"))

        header = self.load(m.group(1), just_header=True)

        if 'location' in header:  #: Direct download link
            self.link = header['location']


    def get_post_parameters(self):
        if self.FORM_PATTERN or self.FORM_INPUTS_MAP:
            action, inputs = self.parse_html_form(self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {})
        else:
            action, inputs = self.parse_html_form(input_names={'op': re.compile(r'^download')})

        if not inputs:
            action, inputs = self.parse_html_form('F1')
            if not inputs:
                self.retry(reason=self.info['error'] if 'error' in self.info else _("TEXTAREA F1 not found"))

        self.log_debug(inputs)

        if 'op' in inputs:
            if "password" in inputs:
                password = self.get_password()
                if password:
                    inputs['password'] = password
                else:
                    self.fail(_("Missing password"))

            if not self.premium:
                m = re.search(self.WAIT_PATTERN, self.html)
                if m:
                    wait_time = int(m.group(1))
                    self.set_wait(wait_time, False)

                self.handle_captcha(inputs)
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


    def handle_captcha(self, inputs):
        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m:
            captcha_url = m.group(1)
            inputs['code'] = self.captcha.decrypt(captcha_url)
            return

        m = re.search(self.CAPTCHA_BLOCK_PATTERN, self.html, re.S)
        if m:
            captcha_div = m.group(1)
            numerals    = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))

            self.log_debug(captcha_div)

            inputs['code'] = "".join(a[1] for a in sorted(numerals, key=lambda num: int(num[0])))

            self.log_debug("Captcha code: %s" % inputs['code'], numerals)
            return

        recaptcha = ReCaptcha(self)
        try:
            captcha_key = re.search(self.RECAPTCHA_PATTERN, self.html).group(1)

        except Exception:
            captcha_key = recaptcha.detect_key()

        else:
            self.log_debug("ReCaptcha key: %s" % captcha_key)

        if captcha_key:
            inputs['recaptcha_response_field'], inputs['recaptcha_challenge_field'] = recaptcha.challenge(captcha_key)
            return

        solvemedia = SolveMedia(self)
        try:
            captcha_key = re.search(self.SOLVEMEDIA_PATTERN, self.html).group(1)

        except Exception:
            captcha_key = solvemedia.detect_key()

        else:
            self.log_debug("SolveMedia key: %s" % captcha_key)

        if captcha_key:
            inputs['adcopy_response'], inputs['adcopy_challenge'] = solvemedia.challenge(captcha_key)
