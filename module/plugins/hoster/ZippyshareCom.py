#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class ZippyshareCom(Hoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __pattern__ = r"(http://)?www?\d{0,2}\.zippyshare.com/v/"
    __version__ = "0.3"
    __description__ = """Zippyshare.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def setup(self):
        self.html = None
        self.wantReconnect = False
        self.multiDL = True


    def process(self, pyfile):
        self.pyfile = pyfile
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

        file_host_pattern = r"http://([^/]*)/v/(\d*)/.*"
        file_host_search = re.search(file_host_pattern, self.pyfile.url)
        if file_host_search is None:
            return False

        file_host = "http://" + file_host_search.group(1)
        file_key = file_host_search.group(2)

        seed_pattern = r"seed: (\d*)"
        seed_search = re.search(seed_pattern, self.html)
        if seed_search is None:
            return False

        file_seed = int(seed_search.group(1))
        time = str((file_seed * 24) % 6743256)

        file_url = file_host + "/download?key=" + str(file_key) + "&time=" + str(time)
        return file_url


    def get_file_name(self):
        if self.html is None:
            self.download_html()
        if not self.wantReconnect:
            file_name = re.search(r'<meta property="og:title" content="([^"]*)" />', self.html).group(1)
            return file_name
        else:
            return self.pyfile.url


    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        if re.search(r'File does not exist on this server', self.html) is not None:
            return False
        else:
            return True
