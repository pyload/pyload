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

import re, json
from module.plugins.internal.SimpleCrypter import SimpleCrypter


class TurbobitNetFolder(SimpleCrypter):
    __name__ = "TurbobitNetFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}.)?turbobit\.net/download/folder/(\w+)"
    __version__ = "0.01"
    __description__ = """Turbobit.net Folder Plugin"""
    __author_name__ = ("pulpe")

    TITLE_PATTERN = r"<img src='/js/lib/grid/icon/folder.png'> (?P<title>.+)</div>"
    GRID_URL = "http://turbobit.net/downloadfolder/gridFile?id_folder="

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        package_name, folder_name = self.getPackageNameAndFolder()

        grid_file = self.load(self.GRID_URL+re.search(self.__pattern__, pyfile.url).group(1), decode=True)

        ret = json.loads(grid_file)
        
        self.package_links = []
        for i in ret['rows']:
            self.package_links.append('http://turbobit.net/'+i['id']+'.html')

        self.logDebug('Package has %d links' % len(self.package_links))

        if self.package_links:
            self.packages = [(package_name, self.package_links, folder_name)]
        else:
            self.fail('Could not extract any links')

