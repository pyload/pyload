# -*- coding: utf-8 -*-

import re

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from pyload.plugin.Crypter import Crypter


class HoerbuchIn(Crypter):
    __name    = "HoerbuchIn"
    __type    = "crypter"
    __version = "0.60"

    __pattern = r'http://(?:www\.)?hoerbuch\.in/(wp/horbucher/\d+/.+/|tp/out\.php\?.+|protection/folder_\d+\.html)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Hoerbuch.in decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de")]


    article = re.compile("http://(?:www\.)?hoerbuch\.in/wp/horbucher/\d+/.+/")
    protection = re.compile("http://(?:www\.)?hoerbuch\.in/protection/folder_\d+.html")


    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(pyfile.url):
            html = self.load(pyfile.url)
            soup = BeautifulSoup(html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

            abookname = soup.find("a", attrs={"rel": "bookmark"}).text
            for a in soup.findAll("a", attrs={"href": self.protection}):
                package = "%s (%s)" % (abookname, a.previousSibling.previousSibling.text[:-1])
                links = self.decryptFolder(a['href'])

                self.packages.append((package, links, package))
        else:
            self.urls = self.decryptFolder(pyfile.url)


    def decryptFolder(self, url):
        m = self.protection.search(url)
        if m is None:
            self.fail(_("Bad URL"))
        url = m.group(0)

        self.pyfile.url = url
        html = self.load(url, post={"viewed": "adpg"})

        links = []
        pattern = re.compile("http://www\.hoerbuch\.in/protection/(\w+)/(.*?)\"")
        for hoster, lid in pattern.findall(html):
            self.req.lastURL = url
            self.load("http://www.hoerbuch.in/protection/%s/%s" % (hoster, lid))
            links.append(self.req.lastEffectiveURL)

        return links
