# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class DataHuFolder(SimpleCrypter):
    __name__ = "DataHuFolder"
    __type__ = "crypter"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?data.hu/dir/\w+'

    __description__ = """Data.hu folder decrypter plugin"""
    __authors__ = [("crash", None),
                   ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r"<a href='(http://data\.hu/get/.+)' target='_blank'>\1</a>"
    TITLE_PATTERN = ur'<title>(.+) Let\xf6lt\xe9se</title>'


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if u'K\xe9rlek add meg a jelsz\xf3t' in self.html:  # Password protected
            password = self.getPassword()
            if password is '':
                self.fail("No password specified, please set right password on Add package form and retry")
            self.logDebug("The folder is password protected', 'Using password: " + password)
            self.html = self.load(pyfile.url, post={'mappa_pass': password}, decode=True)
            if u'Hib\xe1s jelsz\xf3' in self.html:  # Wrong password
                self.fail("Incorrect password, please set right password on Add package form and retry")

        package_name, folder_name = self.getPackageNameAndFolder()

        package_links = re.findall(self.LINK_PATTERN, self.html)
        self.logDebug("Package has %d links" % len(package_links))

        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')
