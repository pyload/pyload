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

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FreakhareComFolder(SimpleCrypter):
    __name__ = "FreakhareComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?freakshare\.com/folder/.+"
    __version__ = "0.01"
    __description__ = """Freakhare.com Folder Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r'<a href="(http://freakshare.com/files/[^"]+)" target="_blank">'
    TITLE_PATTERN = r'Folder:</b> (?P<title>.+)'
    PAGES_PATTERN = r'Pages: +(?P<pages>\d+)'

    def loadPage(self, page_n):
        if not hasattr(self, 'f_id') and not hasattr(self, 'f_md5'):
            m = re.search(r'http://freakshare.com/\?x=folder&f_id=(\d+)&f_md5=(\w+)', self.html)
            if m:
                self.f_id = m.group(1)
                self.f_md5 = m.group(2)
        return self.load('http://freakshare.com/', get={'x': 'folder',
                                                        'f_id': self.f_id,
                                                        'f_md5': self.f_md5,
                                                        'entrys': '20',
                                                        'page': page_n - 1,
                                                        'order': ''}, decode=True)
