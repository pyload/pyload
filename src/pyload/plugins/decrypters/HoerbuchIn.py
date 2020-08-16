# -*- coding: utf-8 -*-
import re

from bs4 import BeautifulSoup

from ..base.decrypter import BaseDecrypter


class HoerbuchIn(BaseDecrypter):
    __name__ = "HoerbuchIn"
    __type__ = "decrypter"
    __version__ = "0.67"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?hoerbuch\.us/(wp/horbucher/\d+/|tp/out\.php\?.+|protection/folder_\d+\.html)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Hoerbuch.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net"), ("mkaay", "mkaay@mkaay.de")]

    article = re.compile(r"http://(?:www\.)?hoerbuch\.us/wp/horbucher/\d+/.+/")
    protection = re.compile(r"http://(?:www\.)?hoerbuch\.us/protection/folder_\d+.html")
    uploaded = re.compile(
        r"http://(?:www\.)?hoerbuch\.us/protection/uploaded/(\w+)\.html"
    )
    hoster_links = re.compile(r"http://(?:www\.)?hoerbuch\.us/wp/goto/Download/\d+/")

    def decrypt(self, pyfile):
        self.pyfile = pyfile

        if self.article.match(pyfile.url):
            html = self.load(pyfile.url)
            soup = BeautifulSoup(
                html, convertEntities=BeautifulSoup.BeautifulStoneSoup.HTML_ENTITIES
            )

            links = []
            for a in soup.findAll("a", attrs={"href": self.hoster_links}):
                for decrypted_link in self.decrypt_folder(a.get("href")):
                    links.append(decrypted_link)

            self.packages.append((pyfile.name, links, pyfile.name))
        else:
            self.links = self.decrypt_folder(pyfile.url)

    def decrypt_folder(self, url):

        m = self.hoster_links.search(url) or self.protection.search(url)

        if m is None:
            self.fail(self._("Bad URL"))
        url = m.group(0)

        if self.hoster_links.match(url):
            self.load(url)
            url = self.req.last_effective_url

        html = self.load(url, post={"viewed": "adpg"})

        self.pyfile.url = url

        links = []

        soup = BeautifulSoup(
            html, convertEntities=BeautifulSoup.BeautifulStoneSoup.HTML_ENTITIES
        )

        for container in soup.findAll("div", attrs={"class": "container"}):
            href = container.a.get("href")

            uploaded = self.uploaded.search(href)
            if uploaded is not None:
                href = "http://uploaded.net/file/{}".format(uploaded.group(1))

            links.append(href)

        return links
