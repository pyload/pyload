# -*- coding: utf-8 -*-
#Testlink: https://goo.im/devs/liquidsmooth/3.x/codina/Nightly/LS-KK-v3.2-2014-08-01-codina.zip
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
    __pattern__ = r"https?://(?:www\.)?goo\.im/.+"
    __version__ = "0.03"
    __description__ = """Goo.im hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'You will be redirected to (?P<N>.+)  in'
    FILE_OFFLINE_PATTERN = r'The file you requested was not found'

    def setup(self):
        self.chunkLimit = 1
        self.multiDL = self.resumeDownload = True

    def handleFree(self):
        self.pyfile.name = self.pyfile.name.split("/")[-1]
        self.logDebug(self.pyfile.name)
        self.html = self.load(self.pyfile.url, cookies=True)
        self.setWait(10)
        self.wait()
        self.download(self.pyfile.url, cookies=True)

getInfo = create_getInfo(GooIm)
