# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
import re

class SpeedLoadOrgFolder(Crypter):
    __name__ = "SpeedLoadOrgFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?speedload\.org/(?P<ID>\w+)~f$"
    __version__ = "0.1"
    __description__ = """Speedload Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        (package_name, folder_name) = self.getPackageNameAndFolder()
        package_links = self.getLinks()

        self.packages = [(package_name, package_links, folder_name)]

    def getPackageNameAndFolder(self):
        title_re = r"Files Within Folder '(?P<title>.+)'"
        m = re.search(title_re, self.html)
        if m is not None:
            name = folder = m.group('title')
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
            return name, folder
        else:
            name = self.pyfile.package().name
            folder = self.pyfile.package().folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
            return name, folder

    def getLinks(self):
        pages = int(re.search('Total Pages (\d)', self.html).group(1))

        link_regex = re.compile('<a href="(http://speedload.org/\w+)"')
        links = link_regex.findall(self.html)

        if pages > 1:
            for p in range(2, pages + 1):
                self.html = self.load(self.pyfile.url + '?page=%d' % p)
                links += link_regex.findall(self.html)

        self.logDebug("Package has %d links" % len(links))
        return links
