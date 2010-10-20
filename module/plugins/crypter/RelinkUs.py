#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import binascii
import re
import urllib

from Crypto.Cipher import AES

from module.plugins.Crypter import Crypter

class RelinkUs(Crypter):
    __name__ = "RelinkUs"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?relink.us/(f|((view|go).php))"
    __version__ = "2.0"
    __description__ = """Relink.us Container Plugin"""
    __author_name__ = ("Sleeper-", "spoob", "fragonib")
    __author_mail__ = ("@nonymous", "spoob@pyload.org", "fragonib@yahoo.es")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"

    def decrypt(self, pyfile):

        # Request page
        self.html = self.load(pyfile.url)
        if not self.file_exists():
            self.offline()

        # Get package name and folder
        (package_name, folder_name) = self.getNameAndFolder()

        # Get package links
        (crypted, jk) = self.getCipherParams()
        package_links = self.getLinks(crypted, jk)

        # Pack
        self.packages = [(package_name, package_links, folder_name)]

    def file_exists(self):
        if "sorry.png" in self.html:
            return False
        return True

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

        return (crypted, jk)

    def getNameAndFolder(self):
        title_re = r'<td class="top">Title</td><td class="top">\|</td><td><span class="info_view_id"><i>(?P<title>.*)</i></span></td>'
        m = re.search(title_re, self.html)
        if m is not None:
            title = m.group('title')
            return (title, title)
        return (self.pyfile.package().name, self.pyfile.package().folder)

    def getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
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

        return links
