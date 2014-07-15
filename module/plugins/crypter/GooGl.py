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

from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads


class GooGl(Crypter):
    __name__ = "GooGl"
    __version__ = "0.01"
    __type__ = "crypter"

    __pattern__ = r'https?://(?:www\.)?goo\.gl/\w+'

    __description__ = """Goo.gl decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    API_URL = "https://www.googleapis.com/urlshortener/v1/url"


    def decrypt(self, pyfile):
        rep = self.load(self.API_URL, get={'shortUrl': pyfile.url})
        self.logDebug('JSON data: ' + rep)
        rep = json_loads(rep)

        if 'longUrl' in rep:
            self.urls = [rep['longUrl']]
        else:
            self.fail('Unable to expand shortened link')
