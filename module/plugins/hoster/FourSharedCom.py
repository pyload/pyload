#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster

class FourSharedCom(Hoster):
    __name__ = "FourSharedCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?4shared(-china)?\.com/(account/)?(download|get|file|document|photo|video|audio)/.+?/.*"
    __version__ = "0.1"
    __description__ = """4Shared Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):

        html = self.load(pyfile.url)
        tmp_link = ""
        link = ""
        name = ""
        wait = 20

        for line in html.splitlines():
            if "dbtn" in line:
                tmp_link = line.split('href="')[1].split('"')[0]
            if '<span id="fileNameTextSpan">' in line:
                name = line.split('<span id="fileNameTextSpan">')[1].split('</span>')[0].strip()

        pyfile.name = name
      
        if tmp_link:
            html = self.load(tmp_link).splitlines()
            for i, line in enumerate(html):
                if "id='divDLStart'" in line:
                    link = html[i+1].split("<a href='")[1].split("'")[0]
                elif '<div class="sec">' in line:
                    wait = int(line.split(">")[1].split("<")[0])

        self.setWait(wait)
        self.wait()

        if link:
            self.download(link)
        else:
            self.offline()