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
###############################################################################

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FiredriveComFolder(SimpleCrypter):
    __name__ = "FiredriveComFolder"
    __version__ = "0.01"
    __type__ = "crypter"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/share/.+'

    __description__ = """Firedrive.com folder decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    LINK_PATTERN = r'<div class="pf_item pf_(file|folder).+?public=\'(.+?)\''
    TITLE_PATTERN = r'>Shared Folder "(?P<title>.+)" | Firedrive<'
    OFFLINE_PATTERN = r'class="sad_face_image"|>No such page here.<'
    TEMP_OFFLINE_PATTERN = r'>(File Temporarily Unavailable|Server Error. Try again later)'


    def getLinks(self):
        return map(lambda x: "http://www.firedrive.com/%s/%s" %
                   ("share" if x[0] == "folder" else "file", x[1]),
                   re.findall(self.LINK_PATTERN, self.html))
