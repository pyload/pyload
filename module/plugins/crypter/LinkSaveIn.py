# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
import base64
import binascii
import re

class LinkSaveIn(Crypter):
    __name__ = "LinkSaveIn"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?linksave.in/([a-z0-9]+)"
    __version__ = "1.0"
    __description__ = """LinkSave.in Crypter Plugin"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"
        
    def decrypt(self, pyfile):

        # Request page
        self.html = self.load(pyfile.url)
        if not self.fileExists():
            self.offline()

        # Handle captcha protection
        self.handleCaptcha()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageNameAndFolder()

        # Get package links
        (crypted, jk) = self.getCipherParams()
        package_links = self.getLinks(crypted, jk)

        # Pack
        self.packages = [(package_name, package_links, folder_name)]

    def fileExists(self):
        if "<title>LinkSave.in - Error 404</title>" in self.html:
            self.log.debug("%s: File not found" % self.__name__)
            return False
        return True
    
    def getPackageNameAndFolder(self):
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.log.debug("%s: Default to pyfile name [%s] and folder [%s] for package" % (self.__name__, name, folder))
        return name, folder

    def handleCaptcha(self):
        if "<b>Captcha:</b>" in self.html:
            id = re.search(r'name="id" value="([^"]+)', self.html).group(1)
            hash = re.search(r'name="hash" value="([^"]+)', self.html).group(1)
            url = re.search(r'src=".(/captcha/cap.php\?hsh=[^"]+)', self.html).group(1)
            value = self.decryptCaptcha("http://linksave.in" + url, forceUser=True)
            self.html = self.load(self.pyfile.url, post={"id": id, "hash": hash, "code": value})
    
    def getCipherParams(self):
            
        # Get jk
        jk_re = r'<INPUT(.*?)NAME="%s"(.*?)VALUE="(?P<jk>.*?)"' % LinkSaveIn._JK_KEY_       
        m = re.search(jk_re, self.html)
        jk = m.group('jk')
        
        # Get crypted
        crypted_re = r'<INPUT(.*?)NAME="%s"(.*?)VALUE="(?P<crypted>.*?)"' % LinkSaveIn._CRYPTED_KEY_       
        m = re.search(crypted_re, self.html)
        crypted = m.group('crypted')

        # Log and return
        self.log.debug("%s: Javascript cipher key function [%s]" % (self.__name__, jk))
        return crypted, jk

    def getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log.debug("%s: JsEngine returns value [%s]" % (self.__name__, jreturn))
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
        self.log.debug("%s: Package has %d links" % (self.__name__, len(links)))
        return links
