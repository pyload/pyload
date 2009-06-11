#!/usr/bin/env python
import re
import time

from Plugin import Plugin

class BluehostTo(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "BluehostTo"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)?bluehost.to/file/"
        props['version'] = "0.1"
        props['description'] = """Bluehost Download PLugin"""
        props['author_name'] = ("RaNaN")
        props['author_mail'] = ("RaNaN@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)
        time.sleep(1.5)
        self.html = self.req.load(url, cookies=True)
        print self.html

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()

        inputs = re.findall(r"(<(input|form)[^>]+)", self.html)
        for i in inputs:
            if re.search(r"name=\"BluehostVers2dl\"",i[0]):
                self.BluehostVers2dl = re.search(r"value=\"([^\"]+)", i[0]).group(1)
            elif re.search(r"name=\"PHPSESSID\"",i[0]):
                self.PHPSESSID = re.search(r"value=\"([^\"]+)", i[0]).group(1)
            elif re.search(r"name=\"DownloadV2Hash\"",i[0]):
                self.DownloadV2Hash = re.search(r"value=\"([^\"]+)", i[0]).group(1)
            elif re.search(r"name=\"access\"",i[0]):
                self.access = re.search(r"value=\"([^\"]+)", i[0]).group(1)
            elif re.search(r"name=\"download\"",i[0]):
                url = re.search(r"action=\"([^\"]+)", i[0]).group(1)

        return url

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        file_name_pattern = r"<center><b>.+: (.+)<\/b><\/center>"
        return re.search(file_name_pattern, self.html).group(1)

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()

        if re.search(r"html", self.html) == None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.req.download(url, location, {'BluehostVers2dl': self.BluehostVers2dl, 'DownloadV2Hash': self.DownloadV2Hash, 'PHPSESSID': self.PHPSESSID, 'access': self.access})