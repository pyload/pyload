# -*- coding: utf-8 -*-

import base64
import binascii
import re

from Crypto.Cipher import AES

from module.plugins.Crypter import Crypter


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.06"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.cc/Container/\w+'

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    # URL_REPLACEMENTS  = [(r'.html$', ""), (r'$', ".html")]  #@TODO: Extend SimpleCrypter

    DLC_LINK_PATTERN = r'<button class="dlcdownload" type="button" title="Download \*.dlc" onclick="DownloadDLC\(\'(.+)\'\);"><i></i><span>dlc<'
    WEBLINK_PATTERN = r"openLink.?'([\w_-]*)',"

    CAPTCHA_PATTERN = r'<img id="nc" src="(.+?)"'
    CIRCLECAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'

    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(http://filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'


    def setup(self):
        self.links = []


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, cookies=True)

        if "content notfound" in self.html: #@pyload-devs: this is _not_ a typo
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

        if not self.pyfile.package().password:
            self.fail(_("Please enter the password in package section and try again"))

        self.html = self.load(self.pyfile.url, post={"password": self.password}, cookies=True)


    def handleCaptcha(self):
        m = re.search(self.CAPTCHA_PATTERN, self.html)
        found = re.search(self.CIRCLECAPTCHA_PATTERN, self.html)

        if m: #normal captcha
            self.logDebug("Captcha-URL: %s" % m.group(1))
            captcha_code = self.decryptCaptcha("http://filecrypt.cc" + m.group(1), forceUser=True, imgtype="gif")
            self.siteWithLinks = self.load(self.pyfile.url, post={"recaptcha_response_field":captcha_code}, decode=True, cookies=True)
        elif found: #circle captcha
            self.logDebug("Captcha-URL: %s" % found.group(1))
            captcha_code = self.decryptCaptcha("http://filecrypt.cc" + found.group(1), forceUser=True, imgtype="gif", result_type='positional')
            self.siteWithLinks = self.load(self.pyfile.url, post={"button.x":captcha_code[0], "button.y":captcha_code[1]}, decode=True, cookies=True)
        else:
            self.logDebug("No captcha found")
            self.siteWithLinks = self.html

        if "recaptcha_image" in self.siteWithLinks:
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
                response = self.load("http://filecrypt.cc/Link/%s.html" % link, cookies=True)
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', response)
                response2 = self.load(link2.group(1), just_header=True, cookies=True)
                self.links.append(response2['location'])

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
