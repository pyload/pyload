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


class UploadedToFolder(SimpleCrypter):
    __name__ = "UploadedToFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)"
    __version__ = "0.3"
    __description__ = """UploadedTo Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    TITLE_PATTERN = r'<title>(?P<title>[^<]+)</title>'

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)

        package_name, folder_name = self.getPackageNameAndFolder()

        m = re.search(self.PLAIN_PATTERN, self.html)
        if m:
            plain_link = 'http://uploaded.net/' + m.group('plain')
        else:
            self.fail('Parse error - Unable to find plain url list')

        self.html = self.load(plain_link)
        package_links = self.html.split('\n')[:-1]
        self.logDebug('Package has %d links' % len(package_links))

        self.packages = [(package_name, package_links, folder_name)]
