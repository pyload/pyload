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

        self.checkCaptcha()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageNameAndFolder()

        # Get package links
        (crypted, jk) = self.getCipherParams()
        package_links = self.getLinks(crypted, jk)

        # Pack
        self.packages = [(package_name, package_links, folder_name)]

    def fileExists(self):
        if "<title>LinkSave.in - Error 404</title>" in self.html:
            self.log.debug("LinkSaveIn: File not found")
            return False
        return True
    
    def getPackageNameAndFolder(self):
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.log.debug("LinkSaveIn: Default to pyfile name [%s] and folder [%s] for package" % (name, folder))
        return (name, folder)
    
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
        self.log.debug("LinkSaveIn: Javascript cipher key function [%s]" % jk)
        return (crypted, jk)

    def getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log.debug("LinkSaveIn: JsEngine returns value [%s]" % jreturn)
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
        self.log.debug("LinkSaveIn: Package has %d links" % len(links))
        return links

    def checkCaptcha(self):

        if "<b>Captcha:</b>" in self.html:

            id = re.search(r'name="id" value="([^"]+)', self.html).group(1)
            hash = re.search(r'name="hash" value="([^"]+)', self.html).group(1)
            url = re.search(r'src=".(/captcha/cap.php\?hsh=[^"]+)', self.html).group(1)

            value = self.decryptCaptcha("http://linksave.in"+url, forceUser=True)

            self.html = self.load(self.pyfile.url, post={"id": id, "hash": hash, "code": value})