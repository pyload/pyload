# -*- coding: utf-8 -*-
#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import binascii
import re
import urlparse

from Crypto.Cipher import AES

from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.ReCaptcha import ReCaptcha


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.16"

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

        self.handlePasswordProtection()
        self.handleCaptcha()
        self.handleMirrorPages()

        for handle in (self.handleCNL, self.handleWeblinks, self.handleDlcContainer):
            handle()
            if self.links:
                self.packages = [(pyfile.package().name, self.links, pyfile.package().name)]
                return


    def handleMirrorPages(self):
        if "mirror=" not in self.siteWithLinks:
            return

        mirror = re.findall(self.MIRROR_PAGE_PATTERN, self.siteWithLinks)

        self.logInfo(_("Found %d mirrors") % len(mirror))

        for i in mirror[1:]:
            self.siteWithLinks = self.siteWithLinks + self.load(i).decode("utf-8", "replace")


    def handlePasswordProtection(self):
        if '<input type="text" name="password"' not in self.html:
            return

        self.logInfo(_("Folder is password protected"))

        password = self.getPassword()

        if not password:
            self.fail(_("Please enter the password in package section and try again"))

        self.html = self.load(self.pyfile.url, post={"password": password})


    def handleCaptcha(self):
        m  = re.search(self.CAPTCHA_PATTERN, self.html)
        m2 = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.html)

        if m:  #: normal captcha
            self.logDebug("Captcha-URL: %s" % m.group(1))

            captcha_code = self.decryptCaptcha(urlparse.urljoin(self.base_url, m.group(1)),
                                               forceUser=True,
                                               imgtype="gif")

            self.siteWithLinks = self.load(self.pyfile.url,
                                           post={'recaptcha_response_field': captcha_code},
                                           decode=True)
        elif m2:  #: circle captcha
            self.logDebug("Captcha-URL: %s" % m2.group(1))

            captcha_code = self.decryptCaptcha('%s%s?c=abc' %(self.base_url, m2.group(1)),
                                               result_type='positional')

            self.siteWithLinks = self.load(self.pyfile.url,
                                           post={'button.x': captcha_code[0], 'button.y': captcha_code[1]},
                                           decode=True)

        else:
            recaptcha   = ReCaptcha(self)
            captcha_key = recaptcha.detect_key()

            if captcha_key:
                response, challenge = recaptcha.challenge(captcha_key)
                self.siteWithLinks  = self.load(self.pyfile.url,
                                                post={'g-recaptcha-response': response},
                                                decode=True)
            else:
                self.logInfo(_("No captcha found"))
                self.siteWithLinks = self.html

        if "recaptcha_image" in self.siteWithLinks or "data-sitekey" in self.siteWithLinks:
            self.invalidCaptcha()
            self.retry()


    def handleDlcContainer(self):
        dlc = re.findall(self.DLC_LINK_PATTERN, self.siteWithLinks)

        if not dlc:
            return

        for i in dlc:
            self.links.append("%s/DLC/%s.dlc" % (self.base_url, i))


    def handleWeblinks(self):
        try:
            weblinks = re.findall(self.WEBLINK_PATTERN, self.siteWithLinks)

            for link in weblinks:
                res   = self.load("%s/Link/%s.html" % (self.base_url, link))
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', res)
                res2  = self.load(link2.group(1), just_header=True)
                self.links.append(res2['location'])

        except Exception, e:
            self.logDebug("Error decrypting weblinks: %s" % e)


    def handleCNL(self):
        try:
            vjk = re.findall('<input type="hidden" name="jk" value="function f\(\){ return \'(.*)\';}">', self.siteWithLinks)
            vcrypted = re.findall('<input type="hidden" name="crypted" value="(.*)">', self.siteWithLinks)

            for i in xrange(len(vcrypted)):
                self.links.extend(self._getLinks(vcrypted[i], vjk[i]))

        except Exception, e:
            self.logDebug("Error decrypting CNL: %s" % e)


    def _getLinks(self, crypted, jk):
        # Get key
        key = binascii.unhexlify(str(jk))

        # Decrypt
        Key  = key
        IV   = key
        obj  = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        # Extract links
        text  = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        return links
