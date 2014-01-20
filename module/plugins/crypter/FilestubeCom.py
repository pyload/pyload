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

class FilestubeCom(SimpleCrypter):
    __name__ = "FilestubeCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}.)?filestube\.(?:com|to)/\w+"
    __version__ = "0.01"
    __description__ = """Filestube.com Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    COPY_PASTE_LINKS = r'<pre id="copy_paste_links".*?>(.*?)</pre>'
    LINK_PATTERN2 = r'<a class="gobut" href="(http://.+?)" title="Download Now!" rel="nofollow"'
    TITLE_PATTERN = r"<title>(?P<title>.+) download"

    def getLinks(self):
      linklist = re.search(self.COPY_PASTE_LINKS, self.html, re.MULTILINE)
      if linklist:
        matches = re.findall('^(.*?)$', linklist)
        return matches
      else:
        matches = re.findall(self.LINK_PATTERN2, self.html)
        if matches:
          return matches
        else:
          raise Exception("no links to extract")
