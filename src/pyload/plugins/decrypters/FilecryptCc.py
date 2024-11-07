# -*- coding: utf-8 -*-

#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import base64
import re
import urllib.parse

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.network.http.http_request import HTTPRequest
from pyload.core.utils.convert import to_str

from ..anticaptchas.CoinHive import CoinHive
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..anticaptchas.CutCaptcha import CutCaptcha

from ..base.decrypter import BaseDecrypter
from ..helpers import replace_patterns


class FilecryptCc(BaseDecrypter):
    __name__ = "FilecryptCc"
    __type__ = "decrypter"
    __version__ = "0.50"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("handle_mirror_pages", "bool", "Handle Mirror Pages", True),
    ]

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    COOKIES = [("filecrypt.cc", "lang", "en")]
    URL_REPLACEMENTS = [(r"filecrypt.co", "filecrypt.cc")]

    DLC_LINK_PATTERN = r'onclick="DownloadDLC\(\'(.+)\'\);">'
    WEBLINK_PATTERN = r"<button onclick=\"[\w\-]+?/\*\d+?\*/\('([\w/-]+?)',"
    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(https?://(?:www\.)?filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'

    #CAPTCHA_PATTERN = r"<h2>Security prompt</h2>"

    INTERNAL_CAPTCHA_PATTERN = r'<img id="nc" .* src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'
    KEY_CAPTCHA_PATTERN = r"<script language=JavaScript src='(http://backs\.keycaptcha\.com/swfs/cap\.js)'"
    SOLVEMEDIA_CAPTCHA_PATTERN = r'<script type="text/javascript" src="(https?://api(?:-secure)?\.solvemedia\.com/papi/challenge.+?)"'
    CUTCAPTCHA_CAPTCHA_KEY_PATTERN = r'''\sCUTCAPTCHA_MISERY_KEY\s*=\s*["']([0-9a-f]{40})["']'''
    CUTCAPTCHA_API_KEY_PATTERN = r'''cutcaptcha\.net/captcha/([0-9a-zA-Z]+)\.js'''

    CAPTCHA_PATTERNS = [
        INTERNAL_CAPTCHA_PATTERN,
        CIRCLE_CAPTCHA_PATTERN,
        KEY_CAPTCHA_PATTERN,
        SOLVEMEDIA_CAPTCHA_PATTERN,
        CUTCAPTCHA_CAPTCHA_KEY_PATTERN,
    ]

    def setup(self):
        self.urls = []

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = HTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.request_factory.get_options(),
            limit=2_000_000,
        )

    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        self.log_info("74 pyfile.url", pyfile.url)

        self.data = self._filecrypt_load_url(pyfile.url)
        self.log_info("plugins/decrypters/FilecryptCc.py: self.data[:1000]", self.data[:1000])

        # @NOTE: "content notfound" is NOT a typo
        if (
            "content notfound" in self.data
            or ">File <strong>not</strong> found<" in self.data
            or
            "<strong>Not Found</strong></h2>" in self.data
        ):
            self.log_info("plugins/decrypters/FilecryptCc.py: offline")
            self.offline()

        self.log_info("plugins/decrypters/FilecryptCc.py: handle_password_protection")
        self.handle_password_protection()

        self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha")
        self.site_with_links = self.handle_captcha(pyfile.url)
        self.log_info("plugins/decrypters/FilecryptCc.py: self.site_with_links", repr(self.site_with_links)[:1000])

        if self.site_with_links is None:
            # FIXME why? captcha should be solved
            self.log_info("plugins/decrypters/FilecryptCc.py: retry_captcha")
            self.retry_captcha()

        elif self.site_with_links == "":
            self.log_info("plugins/decrypters/FilecryptCc.py: retry")
            self.retry()

        if self.config.get("handle_mirror_pages"):
            self.log_info("plugins/decrypters/FilecryptCc.py: handle_mirror_pages")
            self.handle_mirror_pages()

        for handle in (
            self.handle_CNL,
            self.handle_weblinks,
            self.handle_dlc_container,
        ):
            self.log_info("plugins/decrypters/FilecryptCc.py: handle", handle)
            handle()
            if self.urls:
                self.packages = [
                    (pyfile.package().name, self.urls, pyfile.package().name)
                ]
                return

    def handle_mirror_pages(self):
        if "mirror=" not in self.site_with_links:
            return

        mirror = re.findall(self.MIRROR_PAGE_PATTERN, self.site_with_links)

        self.log_info(self._("Found {} mirrors").format(len(mirror)))

        for i in mirror[1:]:
            self.site_with_links = self.site_with_links + self._filecrypt_load_url(i)

    def handle_password_protection(self):
        # <input type="password" name="password" id="p4assw0rt"  autofocus autocomplete="off" placeholder="Enter password">
        if (
            re.search(
                #r'div class="input">\s*<input type="text" name="password" id="p4assw0rt"',
                r'placeholder="Enter password"',
                self.data,
            )
            is None
        ):
            self.log_info("not found password input")
            return

        self.log_info(self._("Folder is password protected"))

        password = self.get_password()

        if not password:
            self.fail(
                self._("Please enter the password in package section and try again")
            )

        self.data = self._filecrypt_load_url(
            self.pyfile.url, post={"pssw": password}
        )

    def search_captcha(self, html):
        for pattern in self.CAPTCHA_PATTERNS:
            if match := re.search(pattern, html):
                self.log_info("plugins/decrypters/FilecryptCc.py: search_captcha: found captcha", repr(match.group(0)))
                return True
        return False

    def handle_captcha(self, submit_url):
        self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha: submit_url", submit_url)
        if self.search_captcha(self.data):
            for handle in (
                self._handle_internal_captcha,
                self._handle_circle_captcha,
                self._handle_solvemedia_captcha,
                self._handle_keycaptcha_captcha,
                self._handle_coinhive_captcha,
                self._handle_recaptcha_captcha,
                self._handle_cutcaptcha_captcha,
            ):

                self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha: handle", handle)

                res = handle(submit_url)

                #self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha: handle -> res[:1000]", repr(res)[:1000])
                self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha: handle -> res", repr(res))
                # res: html code

                if res is None:
                    continue

                elif res == "":
                    return res

                if self.search_captcha(res):
                    self.log_info("plugins/decrypters/FilecryptCc.py: handle_captcha: found another captcha in res")
                    return None

                else:
                    return res

            else:
                self.log_warning(self._("Unknown captcha found, retrying"))
                return ""

        else:
            self.log_info(self._("No captcha found"))
            return self.data

    def _handle_internal_captcha(self, url):
        m = re.search(self.INTERNAL_CAPTCHA_PATTERN, self.data)
        if m is not None:
            captcha_url = urllib.parse.urljoin(self.pyfile.url, m.group(1))

            self.log_debug(f"Internal Captcha URL: {captcha_url}")

            captcha_code = self.captcha.decrypt(captcha_url, input_type="gif")

            return self._filecrypt_load_url(
                url, post={"recaptcha_response_field": captcha_code}
            )

        else:
            return None

    def _handle_circle_captcha(self, url):
        m = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug(
                "Circle Captcha URL: {}".format(
                    urllib.parse.urljoin(self.pyfile.url, m.group(1))
                )
            )

            captcha_url = urllib.parse.urljoin(self.pyfile.url, m.group(1))

            self.log_debug(f"Circle Captcha URL: {captcha_url}")

            """
            FIXME OCR fails to solve captcha

            [2024-09-18 21:03:33]  DEBUG               pyload  DECRYPTER FilecryptCc[3306]: Circle Captcha URL: https://filecrypt.cc/captcha/circle.php
            [2024-09-18 21:03:33]  DEBUG               pyload  DECRYPTER FilecryptCc[3306]: Circle Captcha URL: https://filecrypt.cc/captcha/circle.php
            [2024-09-18 21:03:33]  DEBUG               pyload  ANTICAPTCHA FilecryptCc[3306]: BaseCaptcha | LOAD URL https://filecrypt.cc/captcha/circle.php | get={} | post={} | ref=False | cookies=True | just_header=False | decode=False | multipart=False | redirect=True | req=<src.pyload.core.network.browser.Browser object at 0x7f77fc1c3490>
            [2024-09-18 21:03:34]  INFO                pyload  ANTICAPTCHA FilecryptCc[3306]: BaseCaptcha | Using OCR to decrypt captcha...
            [2024-09-18 21:03:34]  WARNING             pyload  ANTICAPTCHA FilecryptCc[3306]: BaseCaptcha | No OCR result
            """

            captcha_code = self.captcha.decrypt(
                captcha_url, input_type="png", output_type="positional"
            )

            return self._filecrypt_load_url(
                # TODO parse dynamic input name: "button" or "buttonx" or ...
                #url, post={"button.x": captcha_code[0], "button.y": captcha_code[1]}
                url, post={"buttonx.x": captcha_code[0], "buttonx.y": captcha_code[1]}
            )

        else:
            return None

    def _handle_solvemedia_captcha(self, url):
        m = re.search(self.SOLVEMEDIA_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug(
                "Solvemedia Captcha URL: {}".format(
                    urllib.parse.urljoin(self.pyfile.url, m.group(1))
                )
            )

            solvemedia = SolveMedia(self.pyfile)
            captcha_key = solvemedia.detect_key()

            if captcha_key:
                self.captcha = solvemedia
                response, challenge = solvemedia.challenge(captcha_key)

                return self._filecrypt_load_url(
                    url,
                    post={"adcopy_response": response, "adcopy_challenge": challenge},
                )

        else:
            return None

    def _handle_keycaptcha_captcha(self, url):
        m = re.search(self.KEY_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug(
                "Keycaptcha Captcha URL: {} unsupported, retrying".format(m.group(1))
            )
            return ""

        else:
            return None

    def _handle_coinhive_captcha(self, url):
        coinhive = CoinHive(self.pyfile)

        coinhive_key = coinhive.detect_key()
        if coinhive_key:
            self.captcha = coinhive
            token = coinhive.challenge(coinhive_key)

            return self._filecrypt_load_url(url, post={"coinhive-captcha-token": token})

        else:
            return None

    def _handle_recaptcha_captcha(self, url):
        recaptcha = ReCaptcha(self.pyfile)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            self.captcha = recaptcha
            response = recaptcha.challenge(captcha_key)

            return self._filecrypt_load_url(
                url, post={"g-recaptcha-response": response}
            )

        else:
            return None

    def _handle_cutcaptcha_captcha(self, url):
        # based on jdownloader
        # src/org/jdownloader/captcha/v2/challenge/cutcaptcha/AbstractCaptchaHelperCutCaptcha.java
        m = re.search(self.CUTCAPTCHA_CAPTCHA_KEY_PATTERN, self.data)
        if not m:
            return None
        captcha_key = m.group(1)
        m = re.search(self.CUTCAPTCHA_API_KEY_PATTERN, self.data)
        if not m:
            self.log_error("Cutcaptcha: Not found CUTCAPTCHA_API_KEY_PATTERN")
            return None
        api_key = m.group(1)
        # jd: CutCaptchaChallenge(plugin, siteKey, apiKey)
        self.captcha = CutCaptcha(self.pyfile)
        # example: wtFFUUHAxlOI4bNQjRsunHTFPZriu56a
        captcha_token = self.captcha.challenge(captcha_key, api_key)
        self.log_debug(f"Cutcaptcha: captcha_token={captcha_token}")
        return self._filecrypt_load_url(url, post={"cap_token": captcha_token})

    def handle_dlc_container(self):
        m = re.search(r"const (\w+) = DownloadDLC;", self.site_with_links)
        if m is not None:
            self.site_with_links = self.site_with_links.replace(m.group(1), "DownloadDLC")
        dlcs = re.findall(self.DLC_LINK_PATTERN, self.site_with_links)

        if not dlcs:
            return

        for dlc in dlcs:
            self.urls.append(
                urllib.parse.urljoin(self.pyfile.url, "/DLC/{}.dlc".format(dlc))
            )

    def handle_weblinks(self):
        try:
            links = re.findall(self.WEBLINK_PATTERN, self.site_with_links)

            for link in links:
                link = "https://filecrypt.cc/Link/{}.html".format(link)
                for i in range(5):
                    self.data = self._filecrypt_load_url(link)
                    m = re.search(r'https://filecrypt\.cc/index\.php\?Action=Go&id=\w+', self.data)
                    if m is not None:
                        headers = self._filecrypt_load_url(m.group(0), just_header=True)
                        self.urls.append(headers["location"])
                        break

                else:
                    self.log_error(self._("Weblink could not be found"))

        except Exception as exc:
            self.log_debug(f"Error decrypting weblinks: {exc}")

    def handle_CNL(self):
        try:
            m = re.search(r"const (\w+) = CNLPOP;", self.site_with_links)
            if m is not None:
                self.site_with_links = self.site_with_links.replace(m.group(1), "CNLPOP")

            CNLdata = re.findall(
                r'onsubmit="CNLPOP\(\'(.*)\', \'(.*)\', \'(.*)\', \'(.*)\'\);',
                self.site_with_links,
            )
            for index in CNLdata:
                self.urls.extend(self._get_links(index[2], index[1]))

        except Exception as exc:
            self.log_debug(f"Error decrypting CNL: {exc}")

    def _get_links(self, crypted, jk):
        #: Get key and iv
        key = iv = bytes.fromhex(jk)

        #: Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        text = to_str(
            decryptor.update(base64.b64decode(crypted)) + decryptor.finalize()
        )

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = [link for link in text.split("\n") if link]

        return links

    def _filecrypt_load_url(self, *args, **kwargs):
        try:
            return self.load(*args, **kwargs)
        except BadHeader as exc:
            if exc.code == 500:
                return exc.content
            else:
                raise
