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


class FreetexthostCom(SimpleCrypter):
    __name__ = "FreetexthostCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}.)?freetexthost\.com/\w+"
    __version__ = "0.01"
    __description__ = """Freetexthost.com Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def getLinks(self):
        m = re.search(r'<div id="contentsinner">\s*(.+)<div class="viewcount">', self.html, re.DOTALL)
        if not m:
            self.fail('Unable to extract links | Plugin may be out-of-date')
        links = m.group(1)
        return links.strip().split("<br />\r\n")
