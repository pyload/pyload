# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.unescape import unescape

class ArchivTo(Hoster):
    __name__ = "ArchivTo"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?archiv.to/view/divx/"
    __version__ = "0.1"
    __description__ = """Archiv.to Video Download Hoster"""
    __author_name__ = ("Petersilie")
    __author_mail__ = ("None")

    def setup(self):
        self.html = None

    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        # open url (save cookies needed for download)
        self.html = self.load(self.pyfile.url, cookies=True)

    def get_file_url(self):
        # get actual file url for downloading
        file_url = re.search(r"autoplay=\"true\" custommode=\"none\" src=\"(http://.*?)\"", self.html).group(1)
        return file_url

    def get_file_name(self):
        file_name = re.search(r"style=\"color:black;text-decoration:none;font-size:14px;font-weight:bold\">(.*?)</a>", self.html)
        if not file_name:
            file_name = re.search(r"movietitle=\"(.*?)\"", self.html)
        return unescape(file_name.group(1))

    def file_exists(self):
        # check if file still exists
        self.download_html()
        self.load(str(self.pyfile.url), cookies=False)
        if self.get_file_name():
            return True
        return False
