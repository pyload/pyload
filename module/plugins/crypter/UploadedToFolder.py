# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadedToFolder(SimpleCrypter):
    __name__    = "UploadedToFolder"
    __type__    = "crypter"
    __version__ = "0.41"

    __pattern__ = r'http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """UploadedTo decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    NAME_PATTERN = r'<title>(.+?)<'


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)

        package_name, folder_name = self.getPackageNameAndFolder()

        m = re.search(self.PLAIN_PATTERN, self.html)
        if m:
            plain_link = 'http://uploaded.net/' + m.group('plain')
        else:
            self.error(_("Unable to find plain url list"))

        self.html = self.load(plain_link)
        package_links = self.html.split('\n')[:-1]
        self.logDebug("Package has %d links" % len(package_links))

        self.packages = [(package_name, package_links, folder_name)]
