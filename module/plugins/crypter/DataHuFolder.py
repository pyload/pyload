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


class DataHuFolder(SimpleCrypter):
    __name__ = "DataHuFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?data.hu/dir/\w+"
    __version__ = "0.03"
    __description__ = """Data.hu Folder Plugin"""
    __author_name__ = ("crash", "stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r"<a href='(http://data\.hu/get/.+)' target='_blank'>\1</a>"
    TITLE_PATTERN = ur'<title>(?P<title>.+) Let\xf6lt\xe9se</title>'

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if u'K\xe9rlek add meg a jelsz\xf3t' in self.html:  # Password protected
            password = self.getPassword()
            if password is '':
                self.fail("No password specified, please set right password on Add package form and retry")
            self.logDebug('The folder is password protected', 'Using password: ' + password)
            self.html = self.load(pyfile.url, post={'mappa_pass': password}, decode=True)
            if u'Hib\xe1s jelsz\xf3' in self.html:  # Wrong password
                self.fail("Incorrect password, please set right password on Add package form and retry")

        package_name, folder_name = self.getPackageNameAndFolder()

        package_links = re.findall(self.LINK_PATTERN, self.html)
        self.logDebug('Package has %d links' % len(package_links))

        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')
