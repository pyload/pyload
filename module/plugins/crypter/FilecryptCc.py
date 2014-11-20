# -*- coding: utf-8 -*-

import base64
import binascii
import re

from Crypto.Cipher import AES

from module.plugins.Crypter import Crypter


class FilecryptCc(Crypter):
    __name__    = "FilecryptCc"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?filecrypt\.cc/Container/.+'

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    DLC_LINK_PATTERN = r'<button class="dlcdownload" type="button" title="Download \*.dlc" onclick="DownloadDLC\(\'(.+)\'\);"><i></i><span>dlc<'
    WEBLINK_PATTERN = r"openLink.?'([\w_-]*)',"

    CAPTCHA_PATTERN = r'<img id="nc" src="(.+?)"'

    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(http://filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'


    def setup(self):
        self.package_name  = self.package_folder = self.pyfile.package().name
        self.destination   = self.pyfile.package().queue
        self.password      = self.pyfile.package().password
        self.package_links = []


    def decrypt(self, pyfile):
        self.html = self.load(self.pyfile.url, cookies=True)

        if "content not found" in self.html:
            self.offline()

        self.handlePasswordProtection()
        self.handleCaptcha()
        self.handleMirrorPages()
        self.handleCNL()

        if len(self.package_links) > 0:
            self.logDebug("Found %d CNL-Links" % len(self.package_links))
            self.packages = [(self.package_name, self.package_links, self.package_folder)]
            return

        self.handleWeblinks()

        if len(self.package_links) > 0:
            self.logDebug("Found %d Web-Links" % len(self.package_links))
            self.packages = [(self.package_name, self.package_links, self.package_folder)]
            return

        self.handleDlcContainer()


    def handleMirrorPages(self):
        if "mirror=" not in self.siteWithLinks:
            return

        m = re.findall(self.MIRROR_PAGE_PATTERN, self.siteWithLinks)

        self.logInfo(_("Found %d mirrors, will try to catch all links") % len(m))

        for i in m[1:]:
            self.siteWithLinks = self.siteWithLinks + self.load(i, cookies=True).decode("utf-8", "replace")


    def handlePasswordProtection(self):
        if '<input type="text" name="password"' not in self.html:
            return

        self.logInfo(_("Folder is password protected"))

        if not self.password:
            self.fail(_("Please enter the password in package section and try again"))

        self.html = self.load(self.pyfile.url, post={"password": self.password}, cookies=True)


    def handleCaptcha(self):
        m = re.search(self.CAPTCHA_PATTERN, self.html)

        if m:
            self.logDebug("Captcha-URL: " + m.group(1))
            captcha_code = self.decryptCaptcha("http://filecrypt.cc" + m.group(1), forceUser=True, imgtype="gif")
            self.siteWithLinks = self.load(self.pyfile.url, post={"recaptcha_response_field":captcha_code}, decode=True, cookies=True)
        else:
            self.logDebug("No captcha found")
            self.siteWithLinks = self.html

        if "recaptcha_response_field" in self.siteWithLinks:
            self.invalidCaptcha()
            self.retry()


    def handleDlcContainer(self):
        m = re.findall(self.DLC_LINK_PATTERN, self.siteWithLinks)

        if m:
            self.logDebug("Found DLC-Container")
            urls = []
            for i in m:
                urls.append("http://filecrypt.cc/DLC/%s.dlc" % i)
            pid = self.core.api.addPackage(self.package_name, urls, 1)
        else:
            self.fail(_("Unable to find any links"))


    def handleWeblinks(self):
        try:
            weblinks = re.findall(self.WEBLINK_PATTERN, self.siteWithLinks)

            if not weblinks:
                self.logDebug("No weblink found")
                return

            for link in weblinks:
                response = self.load("http://filecrypt.cc/Link/%s.html" % link, cookies=True)
                link2 = re.search('<iframe noresize src="(.*)"></iframe>', response)
                response2 = self.load(link2.group(1), just_header=True, cookies=True)
                self.package_links.append(response2['location'])

        except Exception, e:
            self.logDebug("Error decrypting weblinks: %s" % e)


    def handleCNL(self):
        try:
            vjk = re.findall('<input type="hidden" name="jk" value="function f\(\){ return \'(.*)\';}">', self.siteWithLinks)
            vcrypted = re.findall('<input type="hidden" name="crypted" value="(.*)">', self.siteWithLinks)

            for i in range(0, len(vcrypted)):
                self.package_links.extend(self._getLinks(vcrypted[i], vjk[i]))

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
