import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.utils import parseFileSize


class FileshareInUa(Hoster):
    __name__ = "FileshareInUa"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?fileshare.in.ua/[A-Za-z0-9]+"
    __version__ = "0.01"
    __description__ = """fileshare.in.ua hoster plugin"""
    __author_name__ = ("fwannmacher")
    __author_mail__ = ("felipe@warhammerproject.com")

    HOSTER_NAME = "fileshare.in.ua"
    PATTERN_FILENAME = r'<h3 class="b-filename">(.*?)</h3>'
    PATTERN_FILESIZE = r'<b class="b-filesize">(.*?)</b>'
    PATTERN_OFFLINE = "This file doesn't exist, or has been removed."

    def setup(self):
        self.resumeDownload = self.multiDL = True

    def process(self, pyfile):
        self.pyfile = pyfile
        self.html = self.load(pyfile.url, decode=True)

        if not self._checkOnline():
            self.offline()

        self.pyfile.name = self._getName()

        self.link = self._getLink()

        if not self.link.startswith('http://'):
            self.link = "http://fileshare.in.ua" + self.link

        self.download(self.link)

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
        return re.search("<a href=\"(/get/.+)\" class=\"b-button m-blue m-big\" >", self.html).group(1)


def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url)

        if re.search(FileshareInUa.PATTERN_OFFLINE, html):
            result.append((url, 0, 1, url))
        else:
            name = re.search(FileshareInUa.PATTERN_FILENAME, html)

            if name is None:
                result.append((url, 0, 1, url))
                continue

            name = name.group(1)
            size = re.search(FileshareInUa.PATTERN_FILESIZE, html)
            size = parseFileSize(size.group(1))

            result.append((name, size, 3, url))

    yield result
