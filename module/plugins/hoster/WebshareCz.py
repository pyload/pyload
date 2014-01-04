# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.network.RequestFactory import getRequest


def getInfo(urls):
    h = getRequest()
    for url in urls:
        h.load(url)
        fid = re.search(WebshareCz.__pattern__, url).group('ID')
        api_data = h.load('https://webshare.cz/api/file_info/', post={'ident': fid})
        if 'File not found' in api_data:
            file_info = (url, 0, 1, url)
        else:
            name = re.search('<name>(.+)</name>', api_data).group(1)
            size = re.search('<size>(.+)</size>', api_data).group(1)
            file_info = (name, size, 2, url)
        yield file_info


class WebshareCz(SimpleHoster):
    __name__ = "WebshareCz"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?webshare.cz/(?:#/)?file/(?P<ID>\w+)"
    __version__ = "0.13"
    __description__ = """WebShare.cz hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def handleFree(self):
        api_data = self.load('https://webshare.cz/api/file_link/', post={'ident': self.fid})
        self.logDebug("API data: " + api_data)
        m = re.search('<link>(.+)</link>', api_data)
        if not m:
            self.parseError('Unable to detect direct link')
        direct = m.group(1)
        self.logDebug("Direct link: " + direct)
        self.download(direct, disposition=True)

    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)

        self.fid = re.search(self.__pattern__, self.pyfile.url).group('ID')

        self.load(self.pyfile.url)
        api_data = self.load('https://webshare.cz/api/file_info/', post={'ident': self.fid})

        if 'File not found' in api_data:
            self.offline()
        else:
            self.pyfile.name = re.search('<name>(.+)</name>', api_data).group(1)
            self.pyfile.size = re.search('<size>(.+)</size>', api_data).group(1)

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (self.pyfile.name, self.pyfile.size))
