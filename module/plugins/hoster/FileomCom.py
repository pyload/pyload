# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

# Test links (random.bin):
# http://fileom.com/gycaytyzdw3g/random.bin.html

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class FileomCom(XFileSharingPro):
    __name__ = "FileomCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?fileom\.com/\w+'
    __version__ = "0.01"
    __description__ = """Fileom.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "fileom.com"

    FILE_URL_REPLACEMENTS = [(r'/$', "")]
    SH_COOKIES = [(".fileom.com", "lang", "english")]

    FILE_NAME_PATTERN = r'Filename: <span>(?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'File Size: <span class="size">(?P<S>[\d\.]+) (?P<U>\w+)'

    ERROR_PATTERN = r'class=["\']err["\'][^>]*>(.*?)(?:\'|</)'

    DIRECT_LINK_PATTERN = r"var url2 = '(.+?)';"

    def setup(self):
        self.resumeDownload = self.premium
        self.multiDL = True
        self.chunkLimit = 1


getInfo = create_getInfo(FileomCom)
