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

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GooIm(SimpleHoster):
    __name__ = "GooIm"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?goo\.im/.+"
    __version__ = "0.02"
    __description__ = """Goo.im hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'<h3>Filename: (?P<N>.+)</h3>'
    FILE_OFFLINE_PATTERN = r'The file you requested was not found'

    def setup(self):
        self.chunkLimit = -1
        self.multiDL = self.resumeDownload = True

    def handleFree(self):
        self.html = self.load(self.pyfile.url)
        m = re.search(r'MD5sum: (?P<MD5>[0-9a-z]{32})</h3>', self.html)
        if m:
            self.check_data = {"md5": m.group('MD5')}
        self.setWait(10)
        self.wait()

        header = self.load(self.pyfile.url, just_header=True)
        if header['location']:
            self.logDebug("Direct link: " + header['location'])
            self.download(header['location'])
        else:
            self.parseError("Unable to detect direct download link")


getInfo = create_getInfo(GooIm)
