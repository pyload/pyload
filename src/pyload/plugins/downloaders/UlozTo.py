# -*- coding: utf-8 -*-

import json
import os
import re
import urllib.parse

import pycurl
from pyload.core.utils import parse
from pyload.core.utils.convert import to_bytes

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader
from ..helpers import timestamp


def convert_decimal_prefix(m):
    #: Decimal prefixes used in filesize and traffic
    return (
        "%%.%df" % {"k": 3, "M": 6, "G": 9}[m.group(2)] % float(m.group(1))
    ).replace(".", "")


class UlozTo(SimpleDownloader):
    __name__ = "UlozTo"
    __type__ = "downloader"
    __version__ = "1.52"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz|pinkfile\.cz)/(?:live/)?(?P<ID>[!\w]+/[^/?]*)"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uloz.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("ondrej", "git@ondrej.it"),
        ("astran", "martin.hromadko@gmail.com"),
    ]

    NAME_PATTERN = r"(<p>File <strong>|<title>)(?P<N>.+?)(<| \|)"
    SIZE_PATTERN = r'<span id="fileSize">.*?(?P<S>[\d.,]+\s[kMG]?B)</span>'
    OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'
    TEMP_OFFLINE_PATTERN = r"<title>500 - Internal Server Error</title>"

    URL_REPLACEMENTS = [
        ("http://", "https://"),
        (
            r"(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz|pinkfile\.cz)",
            "ulozto.net",
        ),
    ]

    SIZE_REPLACEMENTS = [(r"([\d.]+)\s([kMG])B", convert_decimal_prefix)]

    CHECK_TRAFFIC = True

    ADULT_PATTERN = r"PINKfile.cz"
    PASSWD_PATTERN = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href=".+?\?disclaimer=1" class="linkVip">'
    TOKEN_PATTERN = r'<input type="hidden" name="_token_" .*?value="(.+?)"'

    def setup(self):
        self.chunk_limit = 16 if self.premium else 1
        self.multi_dl = True
        self.resume_download = True

    def adult_confirmation(self, pyfile):
        if re.search(self.ADULT_PATTERN, self.data):
            adult = True
            self.log_info(self._("Adult content confirmation needed"))

            url = pyfile.url.replace("ulozto.net", "pinkfile.cz")
            self.load(
                "https://pinkfile.cz/porn-disclaimer",
                post={"agree": "Confirm", "_do": "pornDisclaimer-submit"},
            )

            html = self.load(url)
            name = re.search(self.NAME_PATTERN, html).group(2)

            self.pyfile.name = parse.name(name)
            self.data = html

        else:
            adult = False

        return adult

    def handle_free(self, pyfile):
        is_adult = self.adult_confirmation(pyfile)
        domain = "https://pinkfile.cz" if is_adult else "https://ulozto.net"

        #: Let's try to find direct download
        m = re.search(r'<a id="limitedDownloadButton".*?href="(.*?)"', self.data)
        if m:
            self.download(domain + m.group(1))
            return

        m = re.search(r'<a .* data-href="(.*)" class=".*js-free-download-button-dialog.*?"', self.data)
        if not m:
            self.error(self._("Free download button not found"))

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.data = self.load(domain + m.group(1))
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        if not self.data.startswith('{'):
            action, inputs = self.parse_html_form(
                'id="frm-freeDownloadForm-form"'
            )

            self.log_debug("inputs.keys = %s" % inputs.keys())
            #: Get and decrypt captcha
            if all(key in inputs for key in (
                    "captcha_value", "captcha_id", "captcha_key")):
                #: Old version - last seen 9.12.2013
                self.log_debug('Using "old" version')

                captcha_value = self.captcha.decrypt(
                    "https://img.uloz.to/captcha/%s.png" %
                    inputs['captcha_id'])
                self.log_debug(
                    "CAPTCHA ID: " +
                    inputs['captcha_id'] +
                    ", CAPTCHA VALUE: " +
                    captcha_value)

                inputs.update({
                    'captcha_id': inputs['captcha_id'],
                    'captcha_key': inputs['captcha_key'],
                    'captcha_value': captcha_value
                })

            elif all(key in inputs for key in ("captcha_value", "timestamp", "salt", "hash")):
                #: New version - better to get new parameters (like captcha reload) because of image url - since 6.12.2013
                self.log_debug('Using "new" version')

                xapca = self.load("https://ulozto.net/reloadXapca.php",
                                  get={'rnd': timestamp()})
                self.log_debug("xapca: %s" % xapca)

                data = json.loads(xapca)
                captcha_value = self.captcha.decrypt(data['image'])
                self.log_debug(
                    "CAPTCHA HASH: " +
                    data['hash'],
                    "CAPTCHA SALT: %s" %
                    data['salt'],
                    "CAPTCHA VALUE: " +
                    captcha_value)

                inputs.update({
                    'timestamp': data['timestamp'],
                    'salt': data['salt'],
                    'hash': data['hash'],
                    'captcha_value': captcha_value
                })

            elif all(key in inputs for key in ('do', 'cid', 'ts', 'sign', '_token_', 'sign_a', 'adi')):
                # New version 1.4.2016
                self.log_debug('Using "new" > 1.4.2016')

                inputs.update({'do': inputs['do'], '_token_': inputs['_token_'],
                               'ts': inputs['ts'], 'cid': inputs['cid'],
                               'adi': inputs['adi'], 'sign_a': inputs['sign_a'], 'sign': inputs['sign']})

            else:
                self.error(self._("CAPTCHA form changed"))

            jsvars = self.get_json_response(domain + action, inputs)

        else:
            jsvars = json.loads(self.data)
            redirect = jsvars.get('redirectDialogContent')
            if redirect:
                self.data = self.load(domain + redirect)
                action, inputs = self.parse_html_form('id="frm-rateLimitingCaptcha-form')
                if inputs is None:
                    self.error(self._("Captcha form not found"))

                recaptcha = ReCaptcha(pyfile)

                captcha_key = recaptcha.detect_key()
                if captcha_key is None:
                    self.error(self._("ReCaptcha key not found"))

                self.captcha = recaptcha
                response = recaptcha.challenge(captcha_key)

                inputs['g-recaptcha-response'] = response

                jsvars = self.get_json_response(domain + action, inputs)
                if 'slowDownloadLink' not in jsvars:
                    self.retry_captcha()

        self.download(jsvars["slowDownloadLink"])

    def handle_premium(self, pyfile):
        m = re.search("/file/(.+)/", pyfile.url)
        if not m:
            self.error(self._("Premium link not found"))

        premium_url = urllib.parse.urljoin("https://ulozto.net/quickDownload/", m.group(1))
        self.download(premium_url)

    def check_errors(self):
        if self.PASSWD_PATTERN in self.data:
            password = self.get_password()

            if password:
                self.log_info(self._("Password protected link, trying ") + password)
                self.data = self.load(
                    self.pyfile.url,
                    get={"do": "passwordProtectedForm-submit"},
                    post={"password": password, "password_send": "Send"},
                )

                if self.PASSWD_PATTERN in self.data:
                    self.fail(self._("Wrong password"))
            else:
                self.fail(self._("No password found"))

        if re.search(self.VIPLINK_PATTERN, self.data):
            self.data = self.load(self.pyfile.url, get={"disclaimer": "1"})

        return SimpleDownloader.check_errors(self)

    def check_download(self):
        check = self.scan_download(
            {
                "wrong_captcha": b">An error ocurred while verifying the user",
                "offline": re.compile(to_bytes(self.OFFLINE_PATTERN)),
                "passwd": to_bytes(self.PASSWD_PATTERN),
                #: Paralell dl, server overload etc.
                "server_error": to_bytes("<h1>Z Tvého počítače se již stahuje"),
                "not_found": to_bytes("<title>Ulož.to</title>"),
            }
        )

        if check == "wrong_captcha":
            self.captcha.invalid()
            self.retry(msg=self._("Wrong captcha code"))

        elif check == "offline":
            self.offline()

        elif check == "passwd":
            self.fail(self._("Wrong password"))

        elif check == "server_error":
            self.log_error(self._("Server error, try downloading later"))
            self.multi_dl = False
            self.wait(1 * 60 * 60, True)
            self.retry()

        elif check == "not_found":
            self.fail(self._("Server error, file not downloadable"))

        return SimpleDownloader.check_download(self)

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
