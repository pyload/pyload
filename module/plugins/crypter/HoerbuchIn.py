# -*- coding: utf-8 -*-

import re

from module.lib.BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from module.plugins.Crypter import Crypter


class HoerbuchIn(Crypter):
    __name__ = "HoerbuchIn"
    __type__ = "crypter"
    __version__ = "0.6"

    __pattern__ = r'http://(?:www\.)?hoerbuch\.in/(wp/horbucher/\d+/.+/|tp/out.php\?.+|protection/folder_\d+\.html)'

    __description__ = """Hoerbuch.in decrypter plugin"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    article = re.compile("http://(?:www\.)?hoerbuch\.in/wp/horbucher/\d+/.+/")
    protection = re.compile("http://(?:www\.)?hoerbuch\.in/protection/folder_\d+.html")


    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(pyfile.url):
            src = self.load(pyfile.url)
            soup = BeautifulSoup(src, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

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
            self.fail("Bad URL")
        url = m.group(0)

        self.pyfile.url = url
        src = self.req.load(url, post={"viewed": "adpg"})

        links = []
        pattern = re.compile("http://www\.hoerbuch\.in/protection/(\w+)/(.*?)\"")
        for hoster, lid in pattern.findall(src):
            self.req.lastURL = url
            self.load("http://www.hoerbuch.in/protection/%s/%s" % (hoster, lid))
            links.append(self.req.lastEffectiveURL)

        return links
