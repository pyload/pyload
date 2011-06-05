# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
from module.plugins.ReCaptcha import ReCaptcha
import base64
import binascii
import re

class NCryptIn(Crypter):
    __name__ = "NCryptIn"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?ncrypt.in/folder-([^/\?]+)"
    __version__ = "1.21"
    __description__ = """NCrypt.in Crypter Plugin"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"
        
    def setup(self):
        self.html = None
        self.cleanedHtml = None
        self.captcha = False
        self.package = None

    def decrypt(self, pyfile):
        
        # Init
        self.package = pyfile.package()
        
        # Request package
        self.html = self.load(self.pyfile.url)
        self.cleanedHtml = self.removeCrap(self.html)
        if not self.isOnline():
            self.offline()
        
        # Check for protection    
        if self.isProtected():
            self.html = self.unlockProtection()
            self.cleanedHtml = self.removeCrap(self.html)
            self.handleErrors()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageInfo()

        # Extract package links
        package_links = []
        package_links.extend(self.handleWebLinks())
        package_links.extend(self.handleContainers())
        package_links.extend(self.handleCNL2())
        package_links = set(package_links)

        # Pack
        self.packages = [(package_name, package_links, folder_name)]
        
    def removeCrap(self, content):
        patterns = (r'(type="hidden".*?(name=".*?")?.*?value=".*?")',
                    r'display:none;">(.*?)</(div|span)>',
                    r'<div\s+class="jdownloader"(.*?)</div>',
                    r'<iframe\s+style="display:none(.*?)</iframe>')
        for pattern in patterns:
            rexpr = re.compile(pattern, re.DOTALL)
            content = re.sub(rexpr, "", content)
        return content
        
    def isOnline(self):        
        if "Your folder does not exist" in self.cleanedHtml:
            self.logDebug("File not found")
            return False
        return True
    
    def isProtected(self):
        if re.search(r'''<form.*?name.*?protected.*?>''', self.cleanedHtml):
            self.logDebug("Links are protected")
            return True
        return False
    
    def getPackageInfo(self):
        title_re = r'<h2><span.*?class="arrow".*?>(?P<title>[^<]+).*?</span>.*?</h2>'
        m = re.findall(title_re, self.html, re.DOTALL)
        if m is not None:
            title = m[-1].strip()
            name = folder = title
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
        else:
            name = self.package.name
            folder = self.package.folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder
    
    def unlockProtection(self):
        
        postData = {}
                
        form = re.search(r'''<form\ name="protected"(.*?)</form>''', self.cleanedHtml, re.DOTALL).group(1)
        
        # Submit package password
        if "password" in form:
            password = self.getPassword()
            self.logDebug("Submitting password [%s] for protected links" % password)
            postData['password'] = password
        
        # Resolve anicaptcha
        if "anicaptcha" in form:
            self.captcha = True
            self.logDebug("Captcha protected, resolving captcha")
            captchaUri = re.search(r'src="(/temp/anicaptcha/[^"]+)', form).group(1)
            captcha = self.decryptCaptcha("http://ncrypt.in" + captchaUri)
            self.logDebug("Captcha resolved [%s]" % captcha)
            postData['captcha'] = captcha
        
        # Resolve recaptcha           
        if "recaptcha" in form:
            self.captcha = True    
            id = re.search(r'\?k=(.*?)"', form).group(1)
            self.logDebug("Resolving ReCaptcha with key [%s]" % id)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            postData['recaptcha_challenge_field'] = challenge
            postData['recaptcha_response_field'] = code
                   
        # Unlock protection
        postData['submit_protected'] = 'Continue to folder '
        return self.load(self.pyfile.url, post=postData)
        
    def handleErrors(self):
                   
        if "This password is invalid!" in self.cleanedHtml:
            self.logDebug("Incorrect password, please set right password on 'Edit package' form and retry")
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")  

        if self.captcha:          
            if "The securitycheck was wrong!" in self.cleanedHtml:
                self.logDebug("Invalid captcha, retrying")
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()

    def handleWebLinks(self):
        package_links = []
        self.logDebug("Handling Web links")
        
        pattern = r"(http://ncrypt\.in/link-.*?=)"
        links = re.findall(pattern, self.html)
        self.logDebug("Decrypting %d Web links" % len(links))
        for i, link in enumerate(links):
            self.logDebug("Decrypting Web link %d, %s" % (i+1, link))
            try:
                url = link.replace("link-", "frame-")
                link = self.load(url, just_header=True)['location']
                package_links.append(link)
            except Exception, detail:
                self.logDebug("Error decrypting Web link %s, %s" % (link, detail))    
        return package_links
    
    def handleContainers(self):
        package_links = []
        self.logDebug("Handling Container links")
        
        pattern = r"/container/(rsdf|dlc|ccf)/([a-z0-9]+)"
        containersLinks = re.findall(pattern, self.html)
        self.logDebug("Decrypting %d Container links" % len(containersLinks))
        for containerLink in containersLinks:
            link = "http://ncrypt.in/container/%s/%s.%s" % (containerLink[0], containerLink[1], containerLink[0])
            package_links.append(link)
        return package_links
                
    def handleCNL2(self):
        package_links = []
        self.logDebug("Handling CNL2 links")
        
        if 'cnl2_output' in self.cleanedHtml:
            try:
                (vcrypted, vjk) = self._getCipherParams()
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")            
        return package_links
    
    def _getCipherParams(self):
            
        pattern = r'<input.*?name="%s".*?value="(.*?)"'    
            
        # Get jk
        jk_re = pattern % NCryptIn._JK_KEY_       
        vjk = re.findall(jk_re, self.html)
        
        # Get crypted
        crypted_re = pattern % NCryptIn._CRYPTED_KEY_      
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