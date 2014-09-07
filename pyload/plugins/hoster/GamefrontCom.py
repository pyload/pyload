# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugins.Hoster import Hoster
from pyload.utils import parseFileSize


class GamefrontCom(Hoster):
    __name__ = "GamefrontCom"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?gamefront.com/files/[A-Za-z0-9]+'

    __description__ = """Gamefront.com hoster plugin"""
    __author_name__ = "fwannmacher"
    __author_mail__ = "felipe@warhammerproject.com"

    PATTERN_FILENAME = r'<title>(.*?) | Game Front'
    PATTERN_FILESIZE = r'<dt>File Size:</dt>[\n\s]*<dd>(.*?)</dd>'
    PATTERN_OFFLINE = r"This file doesn't exist, or has been removed."


    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = -1

    def process(self, pyfile):
        self.pyfile = pyfile
        self.html = self.load(pyfile.url, decode=True)

        if not self._checkOnline():
            self.offline()

        pyfile.name = self._getName()

        link = self._getLink()

        if not link.startswith('http://'):
            link = "http://www.gamefront.com/" + link

        self.download(link)

    def _checkOnline(self):
        if re.search(self.PATTERN_OFFLINE, self.html):
            return False
        else:
            return True

    def _getName(self):
        name = re.search(self.PATTERN_FILENAME, self.html)
        if name is None:
            self.fail("%s: Plugin broken." % self.__name__)

        return name.group(1)

    def _getLink(self):
        self.html2 = self.load("http://www.gamefront.com/" + re.search("(files/service/thankyou\\?id=[A-Za-z0-9]+)",
                                                                       self.html).group(1))
        return re.search("<a href=\"(http://media[0-9]+\.gamefront.com/.*)\">click here</a>", self.html2).group(1).replace("&amp;", "&")


def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url)

        if re.search(GamefrontCom.PATTERN_OFFLINE, html):
            result.append((url, 0, 1, url))
        else:
            name = re.search(GamefrontCom.PATTERN_FILENAME, html)
            if name is None:
                result.append((url, 0, 1, url))
            else:
                name = name.group(1)
                size = re.search(GamefrontCom.PATTERN_FILESIZE, html)
                size = parseFileSize(size.group(1))

                result.append((name, size, 3, url))

    yield result
