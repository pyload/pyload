# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Hoster import Hoster
from module.unescape import unescape


class AniStreamCom(Hoster):
    __name__    = "AniStreamCom"
    __type__    = "hoster"
    __version__ = "0.1"

    __pattern__ = r'https?://(www\.)?ani-stream\.com/(embed-)?(?P<ID>\w+)(\.html)?'

    __description__ = """ani-stream.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Markus Paeschke", "github@mpaeschke.de")]

    def __init__(self, pyfile):
        super(AniStreamCom, self).__init__(pyfile)
        self.correct_url = None

    def process(self, pyfile):
        self.get_right_url(pyfile)
        self.download_html()
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def get_right_url(self, pyfile):
        url = pyfile.url
        match = re.search(self.__pattern__, url)
        if match:
            self.correct_url = 'https://www.ani-stream.com/embed-%s.html' % match.group(3)

    def download_html(self):
        self.html = self.load(self.correct_url)

    def get_file_url(self):
        match = re.search(r"file: \'(https?://(www\.)?ani-stream\.com/server\.php)(.*)\'", self.html)
        file_url = match.group(1) + match.group(3)
        return file_url

    def get_file_name(self):
        file_name_pattern = r'<meta property="og:title" content="(.*)" />'
        return unescape(re.search(file_name_pattern, self.html).group(1))
