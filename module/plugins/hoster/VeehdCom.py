#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from module.plugins.Hoster import Hoster


class VeehdCom(Hoster):
    __name__ = 'VeehdCom'
    __type__ = 'hoster'
    __pattern__ = r'http://veehd\.com/video/\d+_\S+'
    __config__ = [
        ('filename_spaces', 'bool', "Allow spaces in filename", 'False'),
        ('replacement_char', 'str', "Filename replacement character", '_'),
    ]
    __version__ = '0.23'
    __description__ = """Veehd.com Download Hoster"""
    __author_name__ = ('cat')
    __author_mail__ = ('cat@pyload')

    def _debug(self, msg):
        self.logDebug('[%s] %s' % (self.__name__, msg))

    def setup(self):
        self.html = None
        self.multiDL = True
        self.req.canContinue = True

    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self._debug("Requesting page: %s" % (repr(url),))
        self.html = self.load(url)

    def file_exists(self):
        if self.html is None:
            self.download_html()

        if '<title>Veehd</title>' in self.html:
            return False
        return True

    def get_file_name(self):
        if self.html is None:
            self.download_html()

        match = re.search(r'<title[^>]*>([^<]+) on Veehd</title>', self.html)
        if not match:
            self.fail("video title not found")
        name = match.group(1)

        # replace unwanted characters in filename
        if self.getConfig('filename_spaces'):
            pattern = '[^0-9A-Za-z\.\ ]+'
        else:
            pattern = '[^0-9A-Za-z\.]+'

        name = re.sub(pattern, self.getConfig('replacement_char'),
                      name)
        return name + '.avi'

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        match = re.search(r'<embed type="video/divx" src="(http://([^/]*\.)?veehd\.com/dl/[^"]+)"',
                          self.html)
        if not match:
            self.fail("embedded video url not found")
        file_url = match.group(1)

        return file_url
