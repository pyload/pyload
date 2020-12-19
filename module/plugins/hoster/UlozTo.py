# -*- coding: utf-8 -*-
import os
import re
import urlparse

import pycurl

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json, parse_name, timestamp
from ..internal.SimpleHoster import SimpleHoster


def convert_decimal_prefix(m):
    #: Decimal prefixes used in filesize and traffic
    return ("%%.%df" % {'k': 3, 'M': 6, 'G': 9}[
            m.group(2)] % float(m.group(1))).replace('.', '')


class UlozTo(SimpleHoster):
    __name__ = "UlozTo"
    __type__ = "hoster"
    __version__ = "1.48"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz)/(?:live/)?(?P<ID>[!\w]+/[^/?]*)'

    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("captcha", "Image;Sound", "Captcha recognition", "Image"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Uloz.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("ondrej", "git@ondrej.it"),
                   ("astran", "martin.hromadko@gmail.com")]

    NAME_PATTERN = r'(<p>File <strong>|<title>)(?P<N>.+?)(<| \|)'
    SIZE_PATTERN = r'<span id="fileSize">.*?(?P<S>[\d.,]+\s[kMG]?B)</span>'
    OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'
    TEMP_OFFLINE_PATTERN = r"<title>500 - Internal Server Error</title>"

    URL_REPLACEMENTS = [("http://", "https://"),
                        (r'(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz)', "ulozto.net")]

    SIZE_REPLACEMENTS = [(r'([\d.]+)\s([kMG])B', convert_decimal_prefix)]

    CHECK_TRAFFIC = True

    ADULT_PATTERN = r'PORNfile.cz'
    PASSWD_PATTERN = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href=".+?\?disclaimer=1" class="linkVip">'
    TOKEN_PATTERN = r'<input type="hidden" name="_token_" .*?value="(.+?)"'

    def setup(self):
        self.chunk_limit = 16 if self.premium else 1
        self.multiDL = True
        self.resume_download = True

    def adult_confirmation(self, pyfile):
        if re.search(self.ADULT_PATTERN, self.data):
            adult = True
            self.log_info(_("Adult content confirmation needed"))

            url = pyfile.url.replace("ulozto.net", "pornfile.cz")
            self.load("https://pornfile.cz/porn-disclaimer",
                      post={'agree': "Confirm",
                            '_do': "pornDisclaimer-submit"})

            html = self.load(url)
            name = re.search(self.NAME_PATTERN, html).group(2)

            self.pyfile.name = parse_name(name)
            self.data = html

        else:
            adult = False

        return adult

    def handle_free(self, pyfile):
        is_adult = self.adult_confirmation(pyfile)

        #Let's try to find direct download
        m = re.search(r'<a id="limitedDownloadButton".*?href="(.*?)"', self.data)
        if m:
            domain = "https://pornfile.cz" if is_adult else "https://ulozto.net"
            self.download(domain + m.group(1))
            return

        m = re.search(r'<a .* data-href="(.*)" class=".*js-free-download-button-dialog.*?"', self.data)
        if not m:
            self.error(_("Free download button not found"))

        domain = "https://pornfile.cz" if is_adult else "https://ulozto.net"
        jsvars = self.get_json_response(domain + m.group(1), [])
        redirect = jsvars.get('redirectDialogContent')
        if redirect:
            self.data = self.load(domain + redirect)
            action, inputs = self.parse_html_form('id="frm-rateLimitingCaptcha-form')
            if inputs is None:
                self.error(_("Captcha form not found"))

            recaptcha = ReCaptcha(pyfile)

            captcha_key = recaptcha.detect_key()
            if captcha_key is None:
                self.error(_("ReCaptcha key not found"))

            self.captcha = recaptcha
            response, challenge = recaptcha.challenge(captcha_key)

            inputs['g-recaptcha-response'] = response

            jsvars = self.get_json_response(domain + action, inputs)
            if 'slowDownloadLink' not in jsvars:
                self.retry_captcha()

        self.download(jsvars['slowDownloadLink'])


    def handle_premium(self, pyfile):
        m = re.search("/file/(.+)/", pyfile.url)
        if not m:
            self.error(_("Premium link not found"))

        premium_url = urlparse.urljoin("https://ulozto.net/quickDownload/", m.group(1))
        self.download(premium_url)

    def check_errors(self):
        if self.PASSWD_PATTERN in self.data:
            password = self.get_password()

            if password:
                self.log_info(_("Password protected link, trying ") + password)
                self.data = self.load(self.pyfile.url,
                                      get={'do': "passwordProtectedForm-submit"},
                                      post={'password': password,
                                            'password_send': 'Send'})

                if self.PASSWD_PATTERN in self.data:
                    self.fail(_("Wrong password"))
            else:
                self.fail(_("No password found"))

        if re.search(self.VIPLINK_PATTERN, self.data):
            self.data = self.load(self.pyfile.url, get={'disclaimer': "1"})

        return SimpleHoster.check_errors(self)

    def check_download(self):
        check = self.scan_download({
            'wrong_captcha': ">An error ocurred while verifying the user",
            'offline': re.compile(self.OFFLINE_PATTERN),
            'passwd': self.PASSWD_PATTERN,
            #: Paralell dl, server overload etc.
            'server_error': "<h1>Z Tvého počítače se již stahuje",
            'not_found': "<title>Ulož.to</title>"
        })

        if check == "wrong_captcha":
            self.captcha.invalid()
            self.retry(msg=_("Wrong captcha code"))

        elif check == "offline":
            self.offline()

        elif check == "passwd":
            self.fail(_("Wrong password"))

        elif check == "server_error":
            self.log_error(_("Server error, try downloading later"))
            self.multiDL = False
            self.wait(1 * 60 * 60, True)
            self.retry()

        elif check == "not_found":
            self.fail(_("Server error, file not downloadable"))

        return SimpleHoster.check_download(self)

    def get_json_response(self, url, inputs):
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        res = self.load(url, post=inputs, ref=self.pyfile.url)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        if not res.startswith('{'):
            self.retry(msg=_("Something went wrong"))

        jsonres = json.loads(res)
        if 'formErrorContent' in jsonres:
            self.retry_captcha()

        self.log_debug(url, res)
        return jsonres
