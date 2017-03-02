# -*- coding: utf-8 -*-

import re

import BeautifulSoup

from ..internal.Crypter import Crypter


class HoerbuchIn(Crypter):
    __name__ = "HoerbuchIn"
    __type__ = "crypter"
    __version__ = "0.67"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?hoerbuch\.us/(wp/horbucher/\d+/|tp/out\.php\?.+|protection/folder_\d+\.html)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Hoerbuch.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org"),
                   ("mkaay", "mkaay@mkaay.de")]

    article = re.compile("http://(?:www\.)?hoerbuch\.us/wp/horbucher/\d+/.+/")
    protection = re.compile(
        "http://(?:www\.)?hoerbuch\.us/protection/folder_\d+.html")
    uploaded = re.compile(
        "http://(?:www\.)?hoerbuch\.us/protection/uploaded/(\w+)\.html")
    hoster_links = re.compile(
        "http://(?:www\.)?hoerbuch\.us/wp/goto/Download/\d+/")

    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(pyfile.url):
            html = self.load(pyfile.url)
            soup = BeautifulSoup.BeautifulSoup(
                html, convertEntities=BeautifulSoup.BeautifulStoneSoup.HTML_ENTITIES)

            links = []
            for a in soup.findAll("a", attrs={'href': self.hoster_links}):
                for decrypted_link in self.decrypt_folder(a.get('href')):
                    links.append(decrypted_link)

            self.packages.append((pyfile.name, links, pyfile.name))
        else:
            self.links = self.decrypt_folder(pyfile.url)

    def decrypt_folder(self, url):

        m = self.hoster_links.search(url) or self.protection.search(url)

        if m is None:
            self.fail(_("Bad URL"))
        url = m.group(0)

        if self.hoster_links.match(url):
            self.load(url)
            url = self.req.lastEffectiveURL

        html = self.load(url, post={'viewed': "adpg"})

        self.pyfile.url = url

        links = []

        soup = BeautifulSoup.BeautifulSoup(
            html, convertEntities=BeautifulSoup.BeautifulStoneSoup.HTML_ENTITIES)

        for container in soup.findAll("div", attrs={'class': "container"}):
            href = container.a.get("href")

            uploaded = self.uploaded.search(href)
            if uploaded is not None:
                href = "http://uploaded.net/file/%s" % uploaded.group(1)

            links.append(href)

        return links
