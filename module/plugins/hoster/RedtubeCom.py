# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from module.unescape import unescape


class RedtubeCom(Hoster):
    __name__ = "RedtubeCom"
    __type__ = "hoster"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?redtube\.com/\d+'

    __description__ = """Redtube.com hoster plugin"""
    __author_name__ = "jeix"
    __author_mail__ = "jeix@hasnomail.de"


    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.html:
            self.download_html()

        file_url = unescape(re.search(r'hashlink=(http.*?)"', self.html).group(1))

        return file_url

    def get_file_name(self):
        if not self.html:
            self.download_html()

        return re.search('<title>(.*?)- RedTube - Free Porn Videos</title>', self.html).group(1).strip() + ".flv"

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()

        if re.search(r'This video has been removed.', self.html) is not None:
            return False
        else:
            return True
