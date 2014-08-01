# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster


class YoupornCom(Hoster):
    __name__ = "YoupornCom"
    __type__ = "hoster"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?youporn\.com/watch/.+'

    __description__ = """Youporn.com hoster plugin"""
    __author_name__ = "willnix"
    __author_mail__ = "willnix@pyload.org"


    def process(self, pyfile):
        self.pyfile = pyfile

        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url, post={"user_choice": "Enter"}, cookies=False)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.html:
            self.download_html()

        return re.search(r'(http://download\.youporn\.com/download/\d+\?save=1)">', self.html).group(1)

    def get_file_name(self):
        if not self.html:
            self.download_html()

        file_name_pattern = r"<title>(.*) - Free Porn Videos - YouPorn</title>"
        return re.search(file_name_pattern, self.html).group(1).replace("&amp;", "&").replace("/", "") + '.flv'

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()
        if re.search(r"(.*invalid video_id.*)", self.html) is not None:
            return False
        else:
            return True
