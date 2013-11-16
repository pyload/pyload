#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter
from module.lib.BeautifulSoup import BeautifulSoup, BeautifulStoneSoup


class HoerbuchIn(Crypter):
    __name__ = "HoerbuchIn"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?hoerbuch\.in/(wp/horbucher/\d+/.+/|tp/out.php\?.+|protection/folder_\d+\.html)"
    __version__ = "0.7"
    __description__ = """Hoerbuch.in Container Plugin"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    article = re.compile("http://(www\.)?hoerbuch\.in/wp/horbucher/\d+/.+/")
    protection = re.compile("http://(www\.)?hoerbuch\.in/protection/folder_\d+.html")

    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(self.pyfile.url):
            src = self.load(self.pyfile.url)
            soup = BeautifulSoup(src, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

            abookname = soup.find("a", attrs={"rel": "bookmark"}).text
            for a in soup.findAll("a", attrs={"href": self.protection}):
                package = "%s (%s)" % (abookname, a.previousSibling.previousSibling.text[:-1])
                links = self.decryptFolder(a["href"])

                self.packages.append((package, links, self.pyfile.package().folder))
        else:
            links = self.decryptFolder(self.pyfile.url)

            self.packages.append((self.pyfile.package().name, links, self.pyfile.package().folder))

    def decryptFolder(self, url):
        m = self.protection.search(url)
        if not m:
            self.fail("Bad URL")
        url = m.group(0)

        self.pyfile.url = url
        src = self.req.load(url, post={"viewed": "adpg"})

        links = []
        pattern = re.compile(r'<div class="container"><a href="(.*?)"')
        for hoster_url in pattern.findall(src):
            self.req.lastURL = url
            self.load(hoster_url)
            links.append(self.req.lastEffectiveURL)

        return links
