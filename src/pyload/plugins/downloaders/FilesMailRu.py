# -*- coding: utf-8 -*-
import re

from ..base.downloader import BaseDownloader


class FilesMailRu(BaseDownloader):
    __name__ = "FilesMailRu"
    __type__ = "downloader"
    __version__ = "0.41"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?files\.mail\.ru/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Files.mail.ru downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("oZiRiz", "ich@oziriz.de")]

    def setup(self):
        self.multi_dl = bool(self.account)

    def process(self, pyfile):
        self.data = self.load(pyfile.url)
        self.url_pattern = r'<a href="(.+?)" onclick="return Act\(this\, \'dlink\'\, event\)">(.+?)</a>'

        #: Marks the file as "offline" when the pattern was found on the html-page'''
        if r'<div class="errorMessage mb10">' in self.data:
            self.offline()

        elif r"Page cannot be displayed" in self.data:
            self.offline()

        #: The filename that will be showed in the list (e.g. test.part1.rar)'''
        pyfile.name = self.get_file_name()

        #: Prepare and download'''
        if not self.account:
            self.prepare()
            self.download(self.get_file_url())
            self.my_post_process()
        else:
            self.download(self.get_file_url())
            self.my_post_process()

    def prepare(self):
        """
        You have to wait some seconds.

        Otherwise you will get a 40Byte HTML Page instead of the file you
        expected
        """
        self.wait(10)
        return True

    def get_file_url(self):
        """
        Gives you the URL to the file.

        Extracted from the Files.mail.ru HTML-page stored in self.data
        """
        return (
            re.search(self.url_pattern, self.data)
            .group(0)
            .split('<a href="')[1]
            .split('" onclick="return Act')[0]
        )

    def get_file_name(self):
        """
        Gives you the Name for each file.

        Also extracted from the HTML-Page
        """
        return (
            re.search(self.url_pattern, self.data)
            .group(0)
            .split(', event)">')[1]
            .split("</a>")[0]
        )

    def my_post_process(self):
        #: Searches the file for HTMl-Code. Sometimes the Redirect
        #: doesn't work (maybe a curl Problem) and you get only a small
        #: HTML file and the Download is marked as "finished"
        #: then the download will be restarted. It's only bad for these
        #: who want download a HTML-File (it's one in a million ;-) )
        #
        #: The maximum UploadSize allowed on files.mail.ru at the moment is 100MB
        #: so i set it to check every download because sometimes there are downloads
        #: that contain the HTML-Text and 60MB ZEROs after that in a xyzfile.part1.rar file
        #: (Loading 100MB in to ram is not an option)
        if self.scan_download({"html": "<meta name="}, read_size=50000) == "html":
            self.log_info(
                self._(
                    "There was HTML Code in the Downloaded File ({})...redirect error? The Download will be restarted"
                ).format(self.pyfile.name)
            )
            self.retry()
