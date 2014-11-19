# -*- coding: utf-8 -*-
# Order: CNL-->Web-->DLC

import base64
import binascii
from Crypto.Cipher import AES
import re
import time
from module.plugins.Crypter import Crypter

class FilecryptCc(Crypter):
    __name__ = "FilecryptCc"
    __type__ = "crypter"
    __pattern__ = r"https?://(www\.)?filecrypt.cc/Container/.+"
    __version__ = "0.03"
    __description__ = """Filecrypt.cc Crypter Plugin"""
    __authors__ = [("zapp-brannigan","")]

    DLC_LINK_PATTERN = r"""<button class="dlcdownload" type="button" title="Download \*.dlc" onclick="DownloadDLC\('(.+)'\);"><i></i><span>dlc<"""
    WEBLINK_PATTERN = r"""openLink.?'([\w_-]*)',"""
    CAPTCHA_PATTERN = r"""<img id="nc" src="(.+)" /></div>"""
    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(http://filecrypt.cc/Container/[\w]+\.html\?mirror=[\d]+)">'
    

    def setup(self):
        self.package_name = self.package_folder = self.pyfile.package().name
        self.destination = self.pyfile.package().queue
        self.password = self.pyfile.package().password
        self.package_links = []
    
    def decrypt(self, pyfile):
        self.html = self.load(self.pyfile.url, cookies=True)
        self.isOnline()
        self.handlePasswordProtection()
        self.handleCaptcha()
        self.handleMirrorPages()
        self.handleCNL()
        if len(self.package_links) > 0:
            self.logDebug("Found %s CNL-Links" %len(self.package_links))
            self.packages = [(self.package_name, self.package_links, self.package_folder)]
            return
        self.handleWeblinks()
        if len(self.package_links) > 0:
            self.logDebug("Found %s Web-Links" %len(self.package_links))
            self.packages = [(self.package_name, self.package_links, self.package_folder)]
            return
        self.handleDlcContainer()
        
    def handleMirrorPages(self):
        if "mirror=" in self.siteWithLinks:
            found = re.findall(self.MIRROR_PAGE_PATTERN, self.siteWithLinks)
            self.logInfo("Found %s mirrors, will try to catch all links" %str(len(found)))
            for i in found[1:]:
                self.siteWithLinks = self.siteWithLinks + self.load(i, cookies=True).decode("utf-8","replace")
        else:
            return
    
    def handlePasswordProtection(self):
        if '<input type="text" name="password"' in self.html:
            self.logInfo("Folder is password protected")
            if self.password == "" or self.password is None:
                self.fail("Please enter the password in package section and try again")
            self.html = self.load(self.pyfile.url, post={"password": self.password}, cookies=True)
        else:
            return
        
    def handleCaptcha(self):
        found = re.search(self.CAPTCHA_PATTERN,self.html)
        if found:
            self.logDebug("Captcha-URL: "+found.group(1))
            captcha_code = self.decryptCaptcha("http://filecrypt.cc"+found.group(1), forceUser=True, imgtype="gif")
            self.siteWithLinks = self.load(self.pyfile.url, post={"recaptcha_response_field":captcha_code}, decode=True,cookies=True)
        else:
            self.logDebug("No captcha found")
            self.siteWithLinks = self.html
        if "recaptcha_response_field" in self.siteWithLinks:
            self.logError("Captcha was wrong")
            self.invalidCaptcha()
            self.retry()
            
    def handleDlcContainer(self):
        found = re.findall(self.DLC_LINK_PATTERN,self.siteWithLinks)
        if found:
            self.logDebug("Found DLC-Container")
            urls = []
            for i in found:
                urls.append("http://filecrypt.cc/DLC/%s.dlc" %i)
            pid = self.core.api.addPackage(self.package_name,urls,1)
        else:
            self.fail("Unable to find any links")

    def isOnline(self):
        if "content notfound" in self.html:
            self.offline()
    
    def handleWeblinks(self):
        try:
            weblinks = re.findall(self.WEBLINK_PATTERN,self.siteWithLinks)
            if len(weblinks) == 0:
                self.logDebug("No weblinks found")
                return
            for link in weblinks:
                response = self.load("http://filecrypt.cc/Link/%s.html" %link, cookies=True)
                link2 = re.search('<iframe noresize src="(.*)"></iframe>',response)
                response2 = self.load(link2.group(1),just_header=True, cookies=True)
                self.package_links.append(response2['location'])
        except Exception, detail:
            self.logDebug("Error decrypting weblinks: %s" %detail)
    
    def handleCNL(self):
        try:
            vjk = re.findall('<input type="hidden" name="jk" value="function f\(\){ return \'(.*)\';}">',self.siteWithLinks)
            vcrypted = re.findall('<input type="hidden" name="crypted" value="(.*)">',self.siteWithLinks)
            for i in range(0,len(vcrypted)):
                self.package_links.extend(self._getLinks(vcrypted[i], vjk[i]))
        except Exception, detail:
            self.logDebug("Error decrypting CNL: %s" %detail)

    def _getLinks(self, crypted, jk):
        # Get key
        key     = binascii.unhexlify(str(jk))

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key  = key
        IV   = key
        obj  = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        text  = text.replace("\x00", "").replace("\r", "")
        links = text.split("\n")
        links = filter(lambda x: x != "", links)

        return links
