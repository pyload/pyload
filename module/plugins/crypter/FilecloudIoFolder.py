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

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FilecloudIoFolder(SimpleCrypter):
    __name__ = "FilecloudIoFolder"
    __version__ = "0.01"
    __type__ = "crypter"

    __pattern__ = r'https?://(?:www\.)?(filecloud\.io|ifile\.it)/_\w+'

    __description__ = """Filecloud.io folder decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    LINK_PATTERN = r'href="(http://filecloud.io/\w+)" title'
    TITLE_PATTERN = r'>(?P<title>.+?) - filecloud.io<'
