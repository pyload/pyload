# -*- coding: utf-8 -*-
# http://filecrypt.cc/Container/64E039F859.html
import base64
import binascii
import re

from Crypto.Cipher import AES
from urlparse import urljoin

from module.plugins.Crypter import Crypter
from module.plugins.internal.CaptchaService import ReCaptchaV2


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.10"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.cc/Container/\w+'

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    # URL_REPLACEMENTS  = [(r'.html$', ""), (r'$', ".html")]  #@TODO: Extend SimpleCrypter

    DLC_LINK_PATTERN = r'<button class="dlcdownload" type="button" title="Download \*.dlc" onclick="DownloadDLC\(\'(.+)\'\);"><i></i><span>dlc<'
    WEBLINK_PATTERN  = r"openLink.?'([\w_-]*)',"

    CAPTCHA_PATTERN        = r'<img id="nc" src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'

    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(http://filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'


    def setup(self):
        self.links = []


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, cookies=True)

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
            self.siteWithLinks = self.siteWithLinks + self.load(i, cookies=True).decode("utf-8", "replace")


    def handlePasswordProtection(self):
        if '<input type="text" name="password"' not in self.html:
            return

        self.logInfo(_("Folder is password protected"))

        password = self.getPassword()
        
        if not password:
            self.fail(_("Please enter the password in package section and try again"))

        self.html = self.load(self.pyfile.url, post={"password": password}, cookies=True)


    def handleCaptcha(self):
        m  = re.search(self.CAPTCHA_PATTERN, self.html)
        m2 = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.html)

        if m:  #: normal captcha
            self.logDebug("Captcha-URL: %s" % m.group(1))

            captcha_code = self.decryptCaptcha(urljoin("http://filecrypt.cc", m.group(1)),
                                               forceUser=True,
                                               imgtype="gif")

            self.siteWithLinks = self.load(self.pyfile.url,
                                           post={'recaptcha_response_field': captcha_code},
                                           cookies=True,
                                           decode=True)
        elif m2:  #: circle captcha
            self.logDebug("Captcha-URL: %s" % m2.group(1))

            captcha_code = self.decryptCaptcha(urljoin("http://filecrypt.cc", m2.group(1)),
                                               forceUser=True,
                                               imgtype="gif",
                                               result_type='positional')

            self.siteWithLinks = self.load(self.pyfile.url,
                                           post={'button.x': captcha_code[0], 'button.y': captcha_code[1]},
                                           cookies=True,
                                           decode=True)
                                           
        elif 'class="g-recaptcha"' in self.html:  #: ReCaptchaV2
            captcha = ReCaptchaV2(self)
            response = captcha.doTheCaptcha(self.pyfile.url.split("/")[2])
            self.siteWithLinks = self.load(self.pyfile.url, cookies=True, decode=True, post={"g-recaptcha-response":response})
            
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
            self.links.append("http://filecrypt.cc/DLC/%s.dlc" % i)


    def handleWeblinks(self):
        try:
            weblinks = re.findall(self.WEBLINK_PATTERN, self.siteWithLinks)

            for link in weblinks:
                res   = self.load("http://filecrypt.cc/Link/%s.html" % link, cookies=True)
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', res)
                res2  = self.load(link2.group(1), just_header=True, cookies=True)
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

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key  = key
        IV   = key
        obj  = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        links = filter(lambda x: x != "",
                       text.replace("\x00", "").replace("\r", "").split("\n"))

        return links
