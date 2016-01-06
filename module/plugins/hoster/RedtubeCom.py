# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import html_unescape


class RedtubeCom(Hoster):
    __name__    = "RedtubeCom"
    __type__    = "hoster"
    __version__ = "0.25"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?redtube\.com/\d+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Redtube.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de")]


    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())


    def download_html(self):
        url = self.pyfile.url
        self.data = self.load(url)


    def get_file_url(self):
        """
        Returns the absolute downloadable filepath
        """
        if not self.data:
            self.download_html()

        return html_unescape(re.search(r'hashlink=(http.*?)"', self.data).group(1))


    def get_file_name(self):
        if not self.data:
            self.download_html()

        return re.search('<title>(.*?)- RedTube - Free Porn Videos</title>', self.data).group(1).strip() + ".flv"


    def file_exists(self):
        """
        Returns True or False
        """
        if not self.data:
            self.download_html()

        if re.search(r'This video has been removed.', self.data):
            return False
        else:
            return True
