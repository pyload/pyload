# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
import base64
import binascii
import re

class NCryptIn(Crypter):
    __name__ = "NCryptIn"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?ncrypt.in/folder-([^/\?]+)"
    __version__ = "1.0"
    __description__ = """NCrypt.in Crypter Plugin"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"
        
    def setup(self):
        self.html = None

    def decrypt(self, pyfile):
        
        # Init
        self.pyfile = pyfile
        self.package = pyfile.package()
        
        # Request package
        self.html = self.requestPackage()
        if not self.isOnline():
            self.offline()
        
        # Check for password/captcha protection    
        if self.isProtected():
            self.html = self.unlockProtection()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageInfo()

        # Extract package links
        try:
            package_links = []
            (vcrypted, vjk) = self.getCipherParams()
            for (crypted, jk) in zip(vcrypted, vjk):
                package_links = package_links + self.getLinks(crypted, jk)
        except:
            self.fail("NCryptIn: Unable to decrypt package")

        # Pack
        self.packages = [(package_name, package_links, folder_name)]
        
    def requestPackage(self):
        return self.load(self.pyfile.url)

    def isOnline(self):        
        if "Your folder does not exist" in self.html:
            pattern = r'[^"]*(display\s*\:\s*none)[^"]*'
            m = re.search(pattern, self.html)
            if m is None:
                self.log.debug("NCryptIn: File not found")
                return False
        return True
    
    def isProtected(self):
        pattern = r'''<form.*?name.*?protected.*?>'''
        m = re.search(pattern, self.html)
        if m is not None:
            self.log.debug("NCryptIn: Links are protected")
            return True
        return False
    
    def unlockProtection(self):

        # Gather data
        url = self.pyfile.url        
        post = {'submit_protected' : 'Weiter zum Ordner '}
        
        # Resolve captcha
        if "anicaptcha" in self.html:
            self.log.debug("NCryptIn: Captcha protected, resolving captcha")
            url = re.search(r'src="(/temp/anicaptcha/[^"]+)', self.html).group(1)
            captcha = self.decryptCaptcha("http://ncrypt.in" + url)
            self.log.debug("NCryptIn: Captcha resolved [%s]" % (captcha, ))
            post.update({"captcha" : captcha})
                   
        # Submit package password
        pattern = r'''<input.*?name.*?password.*?>'''
        m = re.search(pattern, self.html)
        if m is not None:
            password = self.package.password
            self.log.debug("NCryptIn: Submitting password [%s] for protected links" % (password,))
            post.update({'password' : password })

        # Unlock protection
        html = self.load(url, {}, post)
        
        # Check for invalid password
        if "This password is invalid!" in html:
            self.log.debug("NCryptIn: Incorrect password, please set right password on 'Edit package' form and retry")
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")
            
        if "The securitycheck was wrong!" in html:
            self.log.debug("NCryptIn: Invalid captcha, retrying")
            html = self.unlockProtection()

        return html

    def getPackageInfo(self):
        title_re = r'<h2><span.*?class="arrow".*?>(?P<title>[^<]+).*?</span>.*?</h2>'
        regex = re.compile(title_re, re.DOTALL)
        m = regex.findall(self.html)
        if m is not None:
            title = m[-1].strip()
            name = folder = title
            self.log.debug("NCryptIn: Found name [%s] and folder [%s] in package info" % (name, folder))
            return (name, folder)
        else:
            name = self.package.name
            folder = self.package.folder
            self.log.debug("NCryptIn: Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
            return (name, folder)

    def getCipherParams(self):
            
        pattern = r'<input.*?name="%s".*?value="(.*?)"'    
            
        # Get jk
        jk_re = pattern % NCryptIn._JK_KEY_       
        vjk = re.findall(jk_re, self.html)
        
        # Get crypted
        crypted_re = pattern % NCryptIn._CRYPTED_KEY_      
        vcrypted = re.findall(crypted_re, self.html)

        # Log and return
        self.log.debug("NCryptIn: Detected crypted blocks [%d]" % len(vcrypted))
        return (vcrypted, vjk)

    def getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log.debug("NCryptIn: JsEngine returns value [%s]" % jreturn)
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
        self.log.debug("NCryptIn: Package has %d links" % len(links))
        return links