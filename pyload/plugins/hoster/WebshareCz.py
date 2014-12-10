# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.SimpleHoster import SimpleHoster


def getInfo(urls):
    for url in urls:
        fid = re.search(WebshareCz.__pattern, url).group('ID')
        api_data = getURL("https://webshare.cz/api/file_info/", post={'ident': fid})

        if 'File not found' in api_data:
            file_info = (url, 0, 1, url)
        else:
            name = re.search('<name>(.+)</name>', api_data).group(1)
            size = re.search('<size>(.+)</size>', api_data).group(1)
            file_info = (name, size, 2, url)

        yield file_info


class WebshareCz(SimpleHoster):
    __name    = "WebshareCz"
    __type    = "hoster"
    __version = "0.14"

    __pattern = r'https?://(?:www\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'

    __description = """WebShare.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def handleFree(self):
        api_data = self.load('https://webshare.cz/api/file_link/', post={'ident': self.fid})

        self.logDebug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m is None:
            self.error(_("Unable to detect direct link"))

        self.download(m.group(1), disposition=True)


    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)

        self.fid = re.match(self.__pattern, self.pyfile.url).group('ID')

        self.load(self.pyfile.url)
        api_data = self.load('https://webshare.cz/api/file_info/', post={'ident': self.fid})

        if 'File not found' in api_data:
            self.offline()
        else:
            self.pyfile.name = re.search('<name>(.+)</name>', api_data).group(1)
            self.pyfile.size = re.search('<size>(.+)</size>', api_data).group(1)

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (self.pyfile.name, self.pyfile.size))
