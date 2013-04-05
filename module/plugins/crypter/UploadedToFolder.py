# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
import re

class UploadedToFolder(Crypter):
    __name__ = "UploadedToFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)"
    __version__ = "0.1"
    __description__ = """UploadedTo Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    TITLE_PATTERN = r'<title>(?P<title>[^<]+)</title>'

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)

        package_name, folder_name = self.getPackageNameAndFolder()

        m = re.search(self.PLAIN_PATTERN, self.html)
        if m:
            plain_link = 'http://uploaded.net/' + m.group('plain')
        else:
            self.fail('Parse error - Unable to find plain url list')

        self.html = self.load(plain_link)
        package_links = self.html.split('\n')[:-1]
        self.logDebug('Package has %d links' % len(package_links))

        self.packages = [(package_name, package_links, folder_name)]

    def getPackageNameAndFolder(self):
        m = re.search(self.TITLE_PATTERN, self.html)
        if m:
            name = folder = m.group('title')
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
            return name, folder
        else:
            name = self.pyfile.package().name
            folder = self.pyfile.package().folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
            return name, folder
