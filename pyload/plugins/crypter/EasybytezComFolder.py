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

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class EasybytezComFolder(SimpleCrypter):
    __name__ = "EasybytezComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?easybytez\.com/users/(?P<ID>\d+/\d+)"
    __version__ = "0.05"
    __description__ = """Easybytez Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_URL_REPLACEMENTS = [(__pattern__, r"http://www.easybytez.com/users/\g<ID>?per_page=10000")]

    LINK_PATTERN = r'<td><a href="(http://www\.easybytez\.com/\w+)" target="_blank">.+(?:</a>)?</td>'
    TITLE_PATTERN = r'<Title>Files of \d+: (?P<title>.+) folder</Title>'
