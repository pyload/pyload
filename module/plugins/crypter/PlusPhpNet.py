# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
import base64
import binascii
import re


class PlusPhpNet(Crypter):
    __name__ = "PlusPhpNet"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?plusphp.net/.*?\?(?:id|c)=(?P<id>\w+)"
    __version__ = "0.1"
    __description__ = """PlusPhp.net Crypter Plugin"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"

    def setup(self):
        self.package = None
        self.html = None
        self.shortUrl = None

    def decrypt(self, pyfile):
        
        # Init
        self.package = pyfile.package()
            
        # Request folder home
        self.requestHome()
        if not self.isOnline():
            self.offline()

        # Prepare package name and folder
        (package_name, folder_name) = self.getPackageInfo()
        
        # Check for folder protection
        self.requestShort()    
        if self.isProtected():
            self.unlockProtection()
            self.handleErrors()

        # Pack and return links
        package_links = self.handleCNL2();
        if not package_links:
            self.fail('Could not extract any links')
        self.packages = [(package_name, package_links, folder_name)]

    def requestHome(self):
        self.html = self.load(self.pyfile.url, decode=True)

    def isOnline(self):
        if "There is no such URL in our database" in self.html:
            self.logDebug("File not found")
            return False
        return True

    def isProtected(self):
        if "RESOLVER CAPTCHA" in self.html:
            return True
        return False

    def getPackageInfo(self):
        title_re = r'<h1 title.*?>(?P<title>.*?)</h1>'
        m = re.search(title_re, self.html, re.DOTALL)
        if m is not None:
            title = m.group('title').strip()
            name = folder = title
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
        else:
            name = self.package.name
            folder = self.package.folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder
    
    def requestShort(self):
        short_url_re = r'<iframe.*?src="(?P<url>.*?)".*?</iframe>'
        self.shortUrl = re.search(short_url_re, self.html, re.DOTALL).group('url')
        self.html = self.load(self.shortUrl, decode=True)  

    def unlockProtection(self):

        # Resolve captcha
        self.logDebug("Captcha protected")
        captcha = self.decryptCaptcha("http://plusphp.net/captcha.php")
        self.logDebug("Captcha resolved [%s]" % captcha)

        # Unlock protection
        postData = {}
        postData['tmptxt'] = captcha
        postData['btget'] = 'Verificar Texto'
        postData['action'] = 'checkdata'
        self.html = self.load(self.shortUrl, post=postData, decode=True)

    def handleErrors(self):

        if "Error en captcha, intentalo nuevamente" in self.html:
            self.logDebug("Invalid captcha, retrying")
            self.invalidCaptcha()
            self.retry()
        else:
            self.correctCaptcha()    

    def handleCNL2(self):

        self.logDebug("Handling CNL2 links")
        package_links = []
        
        if 'cnl2' in self.html:
            try:
                (vcrypted, vjk) = self._getCipherParams()
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")
                
        return package_links

    def _getCipherParams(self):

        # Get jk
        jk_re = r'<form action=".*?jk=(.*?)"'
        vjk = re.findall(jk_re, self.html)

        # Get crypted
        crypted_re = r'<input.*?name="%s".*?value="(.*?)"' % self._CRYPTED_KEY_
        vcrypted = re.findall(crypted_re, self.html)

        # Log and return
        self.logDebug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk

    def _getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.logDebug("JsEngine returns value [%s]" % jreturn)
        key = binascii.unhexlify(jreturn)

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key = key
        IV = key
        obj = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = text.split("\n")
        links = filter(lambda x: x != "", links)

        # Log and return
        self.logDebug("Block has %d links" % len(links))
        return links
