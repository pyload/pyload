# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
import base64
import binascii
import re
import urllib

class RelinkUs(Crypter):
    __name__ = "RelinkUs"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?relink.us/(f/|((view|go).php\?id=))(?P<id>.+)"
    __version__ = "2.2"
    __description__ = """Relink.us Crypter Plugin"""
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
        self.html = self.requestPackageInfo()
        if not self.isOnline():
            self.offline()
        
        # Check for password protection    
        if self.isPasswordProtected():
            self.html = self.submitPassword()
            if self.html is None:
                self.fail("Incorrect password, please set right password on Edit package form and retry")

        # Get package name and folder
        (package_name, folder_name) = self.getPackageNameAndFolder()

        # Get package links
        try:
            (crypted, jk) = self.getCipherParams()
            package_links = self.getLinks(crypted, jk)
        except:
            self.fail("Unable to decrypt package")

        # Pack
        self.packages = [(package_name, package_links, folder_name)]

    def isOnline(self):
        if "sorry.png" in self.html:
            self.log.debug("RelinkUs: File not found")
            return False
        return True
    
    def isPasswordProtected(self):
        if "<h1>Container Protection</h1>" in self.html:
            self.log.debug("RelinkUs: Links are password protected")
            return True
        return False
    
    def requestPackageInfo(self):
        return self.load(self.pyfile.url)
    
    def submitPassword(self):
        # Gather data
        url = self.pyfile.url
        m = re.match(self.__pattern__, url)
        if m is None:
            self.log.debug("RelinkUs: Unable to get package id from url [%s]" % (url))
            return
        id = m.group('id')
        password = self.package.password
                   
        # Submit package password     
        url = "http://www.relink.us/container_password.php?id=" + id
        post = { '#' : '', 'password' : password, 'pw' : 'submit' }
        self.log.debug("RelinkUs: Submitting password [%s] for protected links with id [%s]" % (password, id))
        html = self.load(url, {}, post)
        
        # Check for invalid password
        if "An error occurred!" in html:
            self.log.debug("RelinkUs: Incorrect password, please set right password on Add package form and retry")
            return None
        else:
            return html   

    def getPackageNameAndFolder(self):
        title_re = r'<td class="top">Title</td><td class="top">\|</td><td><span class="info_view_id"><i>(?P<title>.+)</i></span></td>'
        m = re.search(title_re, self.html)
        if m is not None:
            name = folder = m.group('title')
            self.log.debug("RelinkUs: Found name [%s] and folder [%s] in package info" % (name, folder))
            return (name, folder)
        else:
            name = self.package.name
            folder = self.package.folder
            self.log.debug("RelinkUs: Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
            return (name, folder)

    def getCipherParams(self):

        # Get vars dict
        vars = {}
        m = re.search(r'flashVars="(?P<vars>.*)"', self.html)
        text = m.group('vars')
        pairs = text.split('&')
        for pair in pairs:
            index = pair.index('=')
            vars[pair[:index]] = pair[index + 1:]

        # Extract cipher pair
        jk = urllib.unquote(vars[RelinkUs._JK_KEY_].replace("+", " "))
        crypted = vars[RelinkUs._CRYPTED_KEY_]

        # Log and return
        self.log.debug("RelinkUs: Javascript cipher key function [%s]" % jk)
        return (crypted, jk)

    def getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log.debug("RelinkUs: JsEngine returns value key=[%s]" % jreturn)
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
        self.log.debug("RelinkUs: Package has %d links" % len(links))
        return links
