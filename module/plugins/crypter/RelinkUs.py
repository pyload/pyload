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
    __pattern__ = r"http://(www\.)?relink.us/(f|((view|go).php))"
    __version__ = "2.1"
    __description__ = """Relink.us Crypter Plugin"""
    __author_name__ = ("Sleeper-", "spoob", "fragonib")
    __author_mail__ = ("@nonymous", "spoob@pyload.org", "fragonib AT yahoo DOT es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"

    def decrypt(self, pyfile):

        # Request page
        self.html = self.load(pyfile.url)
        if not self.fileExists():
            self.offline()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageNameAndFolder()

        # Get package links
        (crypted, jk) = self.getCipherParams()
        package_links = self.getLinks(crypted, jk)

        # Pack
        self.packages = [(package_name, package_links, folder_name)]

    def fileExists(self):
        if "sorry.png" in self.html:
            self.log.debug("RelinkUs: File not found")
            return False
        return True

    def getPackageNameAndFolder(self):
        title_re = r'<td class="top">Title</td><td class="top">\|</td><td><span class="info_view_id"><i>(?P<title>.+)</i></span></td>'
        m = re.search(title_re, self.html)
        if m is not None:
            name = folder = m.group('title')
            self.log.debug("RelinkUs: Found name [%s] and folder [%s] for package" % (name, folder))
            return (name, folder)
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.log.debug("RelinkUs: Default to pyfile name [%s] and folder [%s] for package" % (name, folder))
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
        self.log.debug("RelinkUs: JsEngine returns value [%s]" % jreturn)
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
