#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
import re

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url, decode=True)
        if re.search(FourSharedCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(FourSharedCom.FILE_SIZE_PATTERN, html)
            if found is not None:
                size, units = float(found.group(1).replace(',','')), found.group(2)
                size = size * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]

            found = re.search(FourSharedCom.FILE_NAME_PATTERN, html)
            if found is not None:
                name = re.sub(r"&#(\d+).", lambda m: unichr(int(m.group(1))), found.group(1))

            if found or size > 0:
                result.append((name, size, 2, url))
    yield result


class FourSharedCom(Hoster):
    __name__ = "FourSharedCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?4shared(-china)?\.com/(account/)?(download|get|file|document|photo|video|audio)/.+?/.*"
    __version__ = "0.2"
    __description__ = """4Shared Download Hoster"""
    __author_name__ = ("jeix", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = '<meta name="title" content="([^"]+)" />'
    FILE_SIZE_PATTERN = '<span title="Size: ([0-9,.]+) (KB|MB|GB)">'
    FILE_OFFLINE_PATTERN = 'The file link that you requested is not valid\.'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):

        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo(pyfile)
        self.handleFree(pyfile)

    def getFileInfo(self, pyfile):
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()

        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if not found: self.fail("Parse error (file name)")
        pyfile.name = re.sub(r"&#(\d+).", lambda m: unichr(int(m.group(1))), found.group(1))

        found = re.search(self.FILE_SIZE_PATTERN, self.html)
        if found is None: self.fail("Parse error (file size)")
        size, units = float(found.group(1).replace(',','')), found.group(2)
        pyfile.size = size * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]

    def handleFree(self, pyfile):
        tmp_link = link = ""
        wait = 20

        for line in self.html.splitlines():
            if "dbtn" in line:
                tmp_link = line.split('href="')[1].split('"')[0]

        if tmp_link:
            self.html = self.load(tmp_link).splitlines()
            for i, line in enumerate(self.html):
                if "id='divDLStart'" in line:
                    link = self.html[i+2].split("<a href='")[1].split("'")[0]
                elif '<div class="sec">' in line:
                    wait = int(line.split(">")[1].split("<")[0])

            self.setWait(wait)
            self.wait()

        if link:
            self.download(link)
        else:
            self.offline()