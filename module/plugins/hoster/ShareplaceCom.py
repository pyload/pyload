# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.plugins.Hoster import Hoster


class ShareplaceCom(Hoster):
    __name__ = "ShareplaceCom"
    __type__ = "hoster"
    __version__ = "0.11"

    __pattern__ = r'(http://)?(?:www\.)?shareplace\.(com|org)/\?\w+'

    __description__ = """Shareplace.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ACCakut", None)]


    def process(self, pyfile):
        self.pyfile = pyfile
        self.prepare()
        self.download(self.get_file_url())


    def prepare(self):
        if not self.file_exists():
            self.offline()

        self.pyfile.name = self.get_file_name()

        wait_time = self.get_waiting_time()
        self.setWait(wait_time)
        self.logDebug("Waiting %d seconds." % wait_time)
        self.wait()


    def get_waiting_time(self):
        if not self.html:
            self.download_html()

        #var zzipitime = 15;
        m = re.search(r'var zzipitime = (\d+);', self.html)
        if m:
            sec = int(m.group(1))
        else:
            sec = 0

        return sec


    def download_html(self):
        url = re.sub("shareplace.com\/\?", "shareplace.com//index1.php/?a=", self.pyfile.url)
        self.html = self.load(url, decode=True)


    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        url = re.search(r"var beer = '(.*?)';", self.html)
        if url:
            url = url.group(1)
            url = unquote(
                url.replace("http://http:/", "").replace("vvvvvvvvv", "").replace("lllllllll", "").replace(
                    "teletubbies", ""))
            self.logDebug("URL: %s" % url)
            return url
        else:
            self.error(_("Absolute filepath not found"))


    def get_file_name(self):
        if not self.html:
            self.download_html()

        return re.search("<title>\s*(.*?)\s*</title>", self.html).group(1)


    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()

        if re.search(r"HTTP Status 404", self.html) is not None:
            return False
        else:
            return True
