# -*- coding: utf-8 -*-
#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import binascii
import re
import urlparse

import Crypto.Cipher.AES

from module.network.HTTPRequest import BadHeader

from ..captcha.CoinHive import CoinHive
from ..captcha.ReCaptcha import ReCaptcha
from ..captcha.SolveMedia import SolveMedia
from ..internal.Crypter import Crypter
from ..internal.misc import BIGHTTPRequest, replace_patterns


class FilecryptCc(Crypter):
    __name__ = "FilecryptCc"
    __type__ = "crypter"
    __version__ = "0.50"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("handle_mirror_pages", "bool", "Handle Mirror Pages", True)]

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    COOKIES = [("filecrypt.cc", "lang", "en")]
    URL_REPLACEMENTS = [(r"filecrypt.co", "filecrypt.cc")]

    DLC_LINK_PATTERN = r'onclick="DownloadDLC\(\'(.+)\'\);">'
    WEBLINK_PATTERN = r"<button onclick=\"[\w\-]+?/\*\d+?\*/\('([\w/-]+?)',"
    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(https?://(?:www\.)?filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'

    CAPTCHA_PATTERN = r'<h2>Security prompt</h2>'
    INTERNAL_CAPTCHA_PATTERN = r'<img id="nc" .* src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'
    KEY_CAPTCHA_PATTERN = r"<script language=JavaScript src='(http://backs\.keycaptcha\.com/swfs/cap\.js)'"
    SOLVEMEDIA_CAPTCHA_PATTERN = r'<script type="text/javascript" src="(https?://api(?:-secure)?\.solvemedia\.com/papi/challenge.+?)"'

    def setup(self):
        self.urls = []

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.requestFactory.getOptions(),
            limit=2000000)

    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        self.data = self._filecrypt_load_url(pyfile.url)

        # @NOTE: "content notfound" is NOT a typo
        if "content notfound" in self.data or ">File <strong>not</strong> found<" in self.data:
            self.offline()

        self.handle_password_protection()

        self.site_with_links = self.handle_captcha(pyfile.url)
        if self.site_with_links is None:
            self.retry_captcha()

        elif self.site_with_links == "":
            self.retry()

        if self.config.get('handle_mirror_pages'):
            self.handle_mirror_pages()

        for handle in (self.handle_CNL,
                       self.handle_weblinks,
                       self.handle_dlc_container):
            handle()
            if self.urls:
                self.packages = [(pyfile.package().name, self.urls, pyfile.package().name)]
                return

    def handle_mirror_pages(self):
        if "mirror=" not in self.site_with_links:
            return

        mirror = re.findall(self.MIRROR_PAGE_PATTERN, self.site_with_links)

        self.log_info(_("Found %d mirrors") % len(mirror))

        for i in mirror[1:]:
            self.site_with_links = self.site_with_links + self._filecrypt_load_url(i)

    def handle_password_protection(self):
        if re.search(r'div class="input">\s*<input type="text" name="password" id="p4assw0rt"', self.data) is None:
            return

        self.log_info(_("Folder is password protected"))

        password = self.get_password()

        if not password:
            self.fail(_("Please enter the password in package section and try again"))

        self.data = self._filecrypt_load_url(self.pyfile.url, post={'password': password})

    def handle_captcha(self, submit_url):
        if re.search(self.CAPTCHA_PATTERN, self.data):
            for handle in (self._handle_internal_captcha,
                           self._handle_circle_captcha,
                           self._handle_solvemedia_captcha,
                           self._handle_keycaptcha_captcha,
                           self._handle_coinhive_captcha,
                           self._handle_recaptcha_captcha):

                res = handle(submit_url)
                if res is None:
                    continue

                elif res == "":
                    return res

                if re.search(self.CAPTCHA_PATTERN, res):
                    return None

                else:
                    return res

            else:
                self.log_warning(_("Unknown captcha found, retrying"))
                return ""

        else:
            self.log_info(_("No captcha found"))
            return self.data

    def _handle_internal_captcha(self, url):
        m = re.search(self.INTERNAL_CAPTCHA_PATTERN, self.data)
        if m is not None:
            captcha_url = urlparse.urljoin(self.pyfile.url, m.group(1))

            self.log_debug("Internal Captcha URL: %s" % captcha_url)

            captcha_code = self.captcha.decrypt(captcha_url, input_type="gif")

            return self._filecrypt_load_url(url,
                                            post={'recaptcha_response_field': captcha_code})

        else:
            return None

    def _handle_circle_captcha(self, url):
        m = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug("Circle Captcha URL: %s" % urlparse.urljoin(self.pyfile.url, m.group(1)))

            captcha_url = urlparse.urljoin(self.pyfile.url, m.group(1))

            self.log_debug("Circle Captcha URL: %s" % captcha_url)

            captcha_code = self.captcha.decrypt(captcha_url, input_type="png", output_type='positional')

            return self._filecrypt_load_url(url,
                                            post={'button.x': captcha_code[0],
                                                  'button.y': captcha_code[1]})

        else:
            return None

    def _handle_solvemedia_captcha(self, url):
        m = re.search(self.SOLVEMEDIA_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug("Solvemedia Captcha URL: %s" % urlparse.urljoin(self.pyfile.url, m.group(1)))

            solvemedia = SolveMedia(self.pyfile)
            captcha_key = solvemedia.detect_key()

            if captcha_key:
                self.captcha = solvemedia
                response, challenge = solvemedia.challenge(captcha_key)

                return self._filecrypt_load_url(url,
                                                post={'adcopy_response': response,
                                                      'adcopy_challenge': challenge})

        else:
            return None

    def _handle_keycaptcha_captcha(self, url):
        m = re.search(self.KEY_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug("Keycaptcha Captcha URL: %s unsupported, retrying" % m.group(1))
            return ""

        else:
            return None

    def _handle_coinhive_captcha(self, url):
        coinhive = CoinHive(self.pyfile)

        coinhive_key = coinhive.detect_key()
        if coinhive_key:
            self.captcha = coinhive
            token = coinhive.challenge(coinhive_key)

            return self._filecrypt_load_url(url,
                                            post={'coinhive-captcha-token': token})

        else:
            return None

    def _handle_recaptcha_captcha(self, url):
        recaptcha = ReCaptcha(self.pyfile)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            self.captcha = recaptcha
            response = recaptcha.challenge(captcha_key)

            return self._filecrypt_load_url(url,
                                            post={'g-recaptcha-response': response})

        else:
            return None

    def handle_dlc_container(self):
        m = re.search(r"const (\w+) = DownloadDLC;", self.site_with_links)
        if m is not None:
            self.site_with_links = self.site_with_links.replace(m.group(1), "DownloadDLC")
        dlcs = re.findall(self.DLC_LINK_PATTERN, self.site_with_links)

        if not dlcs:
            return

        for dlc in dlcs:
            self.urls.append(urlparse.urljoin(self.pyfile.url, "/DLC/%s.dlc" % dlc))

    def handle_weblinks(self):
        try:
            links = re.findall(self.WEBLINK_PATTERN, self.site_with_links)

            for link in links:
                link = "https://filecrypt.cc/Link/%s.html" % link
                for i in range(5):
                    self.data = self._filecrypt_load_url(link)
                    m = re.search(r'https://.filecrypt\.cc/index\.php\?Action=Go&id=\w+', self.data)
                    if m is not None:
                        headers = self._filecrypt_load_url(m.group(0), just_header=True)
                        self.urls.append(headers['location'])
                        break

                else:
                    self.log_error(_("Weblink could not be found"))

        except Exception, e:
            self.log_debug("Error decrypting weblinks: %s" % e)

    def handle_CNL(self):
        try:
            m = re.search(r"const (\w+) = CNLPOP;", self.site_with_links)
            if m is not None:
                self.site_with_links = self.site_with_links.replace(m.group(1), "CNLPOP")

            CNLdata = re.findall('onsubmit="CNLPOP\(\'(.*)\', \'(.*)\', \'(.*)\', \'(.*)\'\);',self.site_with_links)
            for index in CNLdata:
                self.urls.extend(self._get_links(index[2], index[1]))

        except Exception, e:
            self.log_debug("Error decrypting CNL: %s" % e)

    def _get_links(self, crypted, jk):
        #: Get key
        key = binascii.unhexlify(str(jk))

        #: Decrypt
        #Key = key
        #IV = key
        obj = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, key)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        return links

    def _filecrypt_load_url(self, *args, **kwargs):
        try:
            return self.load(*args, **kwargs)
        except BadHeader, e:
            if e.code == 500:
                return e.content
            else:
                raise
