# -*- coding: utf-8 -*-

import re

import BeautifulSoup

from module.plugins.internal.Crypter import Crypter


class HoerbuchIn(Crypter):
    __name__    = "HoerbuchIn"
    __type__    = "crypter"
    __version__ = "0.62"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?hoerbuch\.in/(wp/horbucher/\d+/.+/|tp/out\.php\?.+|protection/folder_\d+\.html)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Hoerbuch.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de")]


    article = re.compile("http://(?:www\.)?hoerbuch\.in/wp/horbucher/\d+/.+/")
    protection = re.compile("http://(?:www\.)?hoerbuch\.in/protection/folder_\d+.html")


    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(pyfile.url):
            html = self.load(pyfile.url)
            soup = BeautifulSoup.BeautifulSoup(html, convertEntities=BeautifulSoup.BeautifulStoneSoup.HTML_ENTITIES)

            abookname = soup.find("a", attrs={'rel': "bookmark"}).text
            for a in soup.findAll("a", attrs={'href': self.protection}):
                package = "%s (%s)" % (abookname, a.previousSibling.previousSibling.text[:-1])
                links = self.decrypt_folder(a['href'])

                self.packages.append((package, links, package))
        else:
            self.urls = self.decrypt_folder(pyfile.url)


    def decrypt_folder(self, url):
        m = self.protection.search(url)
        if m is None:
            self.fail(_("Bad URL"))
        url = m.group(0)

        self.pyfile.url = url
        html = self.load(url, post={'viewed': "adpg"})

        links = []
        pattern = re.compile("http://www\.hoerbuch\.in/protection/(\w+)/(.*?)\"")
        for hoster, lid in pattern.findall(html):
            self.req.lastURL = url
            self.load("http://www.hoerbuch.in/protection/%s/%s" % (hoster, lid))
            links.append(self.req.lastEffectiveURL)

        return links
