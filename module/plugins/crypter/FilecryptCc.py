# -*- coding: utf-8 -*-
#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import binascii
import re
import urlparse

import Crypto.Cipher

from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.captcha.SolveMedia import SolveMedia


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.cc/Container/\w+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"      ),
                       ("GammaC0de"     , "nitzo2001[AT]yahoo[DOT]com")]


    # URL_REPLACEMENTS  = [(r'.html$', ""), (r'$', ".html")]  #@TODO: Extend SimpleCrypter

    COOKIES          = [("filecrypt.cc", "lang", "en")]

    DLC_LINK_PATTERN = r'onclick="DownloadDLC\(\'(.+)\'\);">'
    WEBLINK_PATTERN  = r"openLink.?'([\w\-]*)',"

    CAPTCHA_PATTERN          = r'class="safety">Security prompt<'
    INTERNAL_CAPTCHA_PATTERN = r'<img id="nc" src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN   = r'<input type="image" src="(.+?)"'
    KEY_CAPTCHA_PATTERN      = r"<script language=JavaScript src='(http://backs\.keycaptcha\.com/swfs/cap\.js)'"
    SOLVE_MEDIA_PATTERN      = r'<script type="text/javascript" src="(http://api\.solvemedia\.com/papi/challenge.+?)"'

    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(https?://(?:www\.)?filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'


    def setup(self):
        self.urls = []


    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        if "content notfound" in self.data:  #@NOTE: "content notfound" is NOT a typo
            self.offline()

        self.handle_password_protection()
        self.handle_captcha()
        self.handle_mirror_pages()

        for handle in (self.handle_CNL, self.handle_weblinks, self.handle_dlc_container):
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
            self.site_with_links = self.site_with_links + self.load(i)


    def handle_password_protection(self):
        if '<input type="text" name="password"' not in self.data:
            return

        self.log_info(_("Folder is password protected"))

        password = self.get_password()

        if not password:
            self.fail(_("Please enter the password in package section and try again"))

        self.data = self.load(self.pyfile.url, post={'password': password})


    def handle_captcha(self):
        if re.search(self.CAPTCHA_PATTERN, self.data):
            m1  = re.search(self.INTERNAL_CAPTCHA_PATTERN, self.data)
            m2 = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.data)
            m3 = re.search(self.SOLVE_MEDIA_PATTERN, self.data)
            m4 = re.search(self.KEY_CAPTCHA_PATTERN, self.data)

            if m1:  #: Normal captcha
                self.log_debug("Internal Captcha URL: %s" % urlparse.urljoin(self.pyfile.url, m1.group(1)))

                captcha_code = self.captcha.decrypt(urlparse.urljoin(self.pyfile.url, m1.group(1)),
                                                    ref=True, input_type="gif")

                self.site_with_links = self.load(self.pyfile.url,
                                                 post={'recaptcha_response_field': captcha_code})

            elif m2:  #: Circle captcha
                self.log_debug("Circle Captcha URL: %s" % urlparse.urljoin(self.pyfile.url, m2.group(1)))

                captcha_code = self.captcha.decrypt(urlparse.urljoin(self.pyfile.url, m2.group(1)),
                                                    input_type="png", output_type='positional')

                self.site_with_links = self.load(self.pyfile.url,
                                                 post={'button.x': captcha_code[0],
                                                       'button.y': captcha_code[1]})

            elif m3:  #: Solvemedia captcha
                self.log_debug("Solvemedia Captcha URL: %s" % urlparse.urljoin(self.pyfile.url, m3.group(1)))

                solvemedia  = SolveMedia(self.pyfile)
                captcha_key = solvemedia.detect_key()

                if captcha_key:
                    self.captcha = solvemedia
                    response, challenge = solvemedia.challenge(captcha_key)
                    self.site_with_links  = self.load(self.pyfile.url,
                                                      post={'adcopy_response'  : response,
                                                            'adcopy_challenge' : challenge})

            elif m4:  #: Keycaptcha captcha
                self.log_debug("Keycaptcha Captcha URL: %s unsupported, retrying" % m4.group(1))
                self.retry()

            else:
                recaptcha   = ReCaptcha(self.pyfile)
                captcha_key = recaptcha.detect_key()

                if captcha_key:
                    self.captcha = recaptcha

                    try:
                        response, challenge = recaptcha.challenge(captcha_key)

                    except Exception:
                        self.retry_captcha()

                    self.site_with_links  = self.load(self.pyfile.url,
                                                      post={'g-recaptcha-response': response})
                else:
                    self.log_info(_("Unknown captcha found, retrying"))
                    self.retry()

            if re.search(self.CAPTCHA_PATTERN, self.site_with_links):
                self.retry_captcha()

        else:
            self.log_info(_("No captcha found"))
            self.site_with_links = self.data



    def handle_dlc_container(self):
        dlcs = re.findall(self.DLC_LINK_PATTERN, self.site_with_links)

        if not dlcs:
            return

        for _dlc in dlcs:
            self.urls.append(urlparse.urljoin(self.pyfile.url, "/DLC/%s.dlc" % _dlc))


    def handle_weblinks(self):
        try:
            links = re.findall(self.WEBLINK_PATTERN, self.site_with_links)

            for _link in links:
                res   = self.load(urlparse.urljoin(self.pyfile.url, "/Link/%s.html" % _link))
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', res)
                if link2:
                    res2  = self.load(link2.group(1), just_header=True)
                    self.urls.append(res2['location'])

        except Exception, e:
            self.log_debug("Error decrypting weblinks: %s" % e)


    def handle_CNL(self):
        try:
            vjk = re.findall('<input type="hidden" name="jk" value="function f\(\){ return \'(.*)\';}">', self.site_with_links)
            vcrypted = re.findall('<input type="hidden" name="crypted" value="(.*)">', self.site_with_links)

            for i in xrange(len(vcrypted)):
                self.urls.extend(self._get_links(vcrypted[i], vjk[i]))

        except Exception, e:
            self.log_debug("Error decrypting CNL: %s" % e)


    def _get_links(self, crypted, jk):
        #: Get key
        key = binascii.unhexlify(str(jk))

        #: Decrypt
        Key  = key
        IV   = key
        obj  = Crypto.Cipher.AES.new(Key, Crypto.Cipher.AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text  = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        return links
