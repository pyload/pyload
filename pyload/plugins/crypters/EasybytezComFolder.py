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
    __pattern__ = r"https?://(www\.)?easybytez\.com/users/\w+/\w+"
    __version__ = "0.02"
    __description__ = """Easybytez Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r'<div class="link"><a href="(http://www\.easybytez\.com/\w+)" target="_blank">.+</a></div>'
    TITLE_PATTERN = r'<Title>Files of (?P<title>.+) folder</Title>'
    PAGES_PATTERN = r"<a href='[^']+'>(?P<pages>\d+)</a><a href='[^']+'>Next &#187;</a><br><small>\(\d+ total\)</small></div>"

    def loadPage(self, page_n):
        return self.load(self.pyfile.url, get={'page': page_n}, decode=True)
