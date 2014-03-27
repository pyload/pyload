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

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class TusfilesNet(XFileSharingPro):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?(tusfiles\.net)/(?P<ID>\w+)'
    __version__ = "0.03"
    __description__ = """Tusfiles.net hoster plugin"""
    __author_name__ = ("stickell", "Walter Purcaro")
    __author_mail__ = ("l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<li>(?P<N>.+)</li>\s+<li><b>\w+:</b> <small>(?P<S>[\d.]+) (?P<U>\w+)</small></li>'
    FILE_OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!'

    SH_COOKIES = [(".tusfiles.net", "lang", "english")]

    def setup(self):
        self.multiDL = False
        self.chunkLimit = -1
        self.resumeDownload = True


getInfo = create_getInfo(TusfilesNet)
