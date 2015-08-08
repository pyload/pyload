# -*- coding: utf-8 -*-
#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import binascii
import re
import urlparse

from Crypto.Cipher import AES

from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.ReCaptcha import ReCaptcha


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.18"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.cc/Container/\w+'

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    # URL_REPLACEMENTS  = [(r'.html$', ""), (r'$', ".html")]  #@TODO: Extend SimpleCrypter

    DLC_LINK_PATTERN = r'<button class="dlcdownload" type="button" title="Download \*.dlc" onclick="DownloadDLC\(\'(.+)\'\);"><i></i><span>dlc<'
    WEBLINK_PATTERN  = r"openLink.?'([\w_-]*)',"

    CAPTCHA_PATTERN        = r'<img id="nc" src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'

    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(https?://(?:www\.)?filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'


    def setup(self):
        self.links = []


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        self.base_url = self.pyfile.url.split("Container")[0]

        if "content notfound" in self.html:  #@NOTE: "content notfound" is NOT a typo
            self.offline()

        self.handle_password_protection()
        self.handle_captcha()
        self.handle_mirror_pages()

        for handle in (self.handle_CNL, self.handle_weblinks, self.handle_dlc_container):
            handle()
            if self.links:
                self.packages = [(pyfile.package().name, self.links, pyfile.package().name)]
                return


    def handle_mirror_pages(self):
        if "mirror=" not in self.site_with_links:
            return

        mirror = re.findall(self.MIRROR_PAGE_PATTERN, self.site_with_links)

        self.log_info(_("Found %d mirrors") % len(mirror))

        for i in mirror[1:]:
            self.site_with_links = self.site_with_links + self.load(i)


    def handle_password_protection(self):
        if '<input type="text" name="password"' not in self.html:
            return

        self.log_info(_("Folder is password protected"))

        password = self.get_password()

        if not password:
            self.fail(_("Please enter the password in package section and try again"))

        self.html = self.load(self.pyfile.url, post={'password': password})


    def handle_captcha(self):
        m  = re.search(self.CAPTCHA_PATTERN, self.html)
        m2 = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.html)

        if m:  #: Normal captcha
            self.log_debug("Captcha-URL: %s" % m.group(1))

            captcha_code = self.captcha.decrypt(urlparse.urljoin(self.base_url, m.group(1)),
                                                input_type="gif")

            self.site_with_links = self.load(self.pyfile.url,
                                           post={'recaptcha_response_field': captcha_code})
        elif m2:  #: Circle captcha
            self.log_debug("Captcha-URL: %s" % m2.group(1))

            captcha_code = self.captcha.decrypt('%s%s?c=abc' %(self.base_url, m2.group(1)),
                                               output_type='positional')

            self.site_with_links = self.load(self.pyfile.url,
                                           post={'button.x': captcha_code[0], 'button.y': captcha_code[1]})

        else:
            recaptcha   = ReCaptcha(self)
            captcha_key = recaptcha.detect_key()

            if captcha_key:
                response, challenge = recaptcha.challenge(captcha_key)
                self.site_with_links  = self.load(self.pyfile.url,
                                                post={'g-recaptcha-response': response})
            else:
                self.log_info(_("No captcha found"))
                self.site_with_links = self.html

        if "recaptcha_image" in self.site_with_links or "data-sitekey" in self.site_with_links:
            self.captcha.invalid()
            self.retry()


    def handle_dlc_container(self):
        dlc = re.findall(self.DLC_LINK_PATTERN, self.site_with_links)

        if not dlc:
            return

        for i in dlc:
            self.links.append("%s/DLC/%s.dlc" % (self.base_url, i))


    def handle_weblinks(self):
        try:
            weblinks = re.findall(self.WEBLINK_PATTERN, self.site_with_links)

            for link in weblinks:
                res   = self.load("%s/Link/%s.html" % (self.base_url, link))
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', res)
                res2  = self.load(link2.group(1), just_header=True)
                self.links.append(res2['location'])

        except Exception, e:
            self.log_debug("Error decrypting weblinks: %s" % e)


    def handle_CNL(self):
        try:
            vjk = re.findall('<input type="hidden" name="jk" value="function f\(\){ return \'(.*)\';}">', self.site_with_links)
            vcrypted = re.findall('<input type="hidden" name="crypted" value="(.*)">', self.site_with_links)

            for i in xrange(len(vcrypted)):
                self.links.extend(self._get_links(vcrypted[i], vjk[i]))

        except Exception, e:
            self.log_debug("Error decrypting CNL: %s" % e)


    def _get_links(self, crypted, jk):
        #: Get key
        key = binascii.unhexlify(str(jk))

        #: Decrypt
        Key  = key
        IV   = key
        obj  = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text  = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        return links
