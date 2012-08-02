# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from module.plugins.hoster.CoolshareCz import CoolshareCz
from module.plugins.internal.SimpleHoster import create_getInfo

class WarserverCz(CoolshareCz):
    __name__ = "WarserverCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?warserver.cz/stahnout/(?P<ID>\d+)/.+"
    __version__ = "0.1"
    __description__ = """Warserver.cz"""
    __author_name__ = ("zoidberg")
   
    PREMIUM_URL_PATTERN = r'<a href="(http://s01.warserver.cz/dwn-premium.php.*?)"'
    DOMAIN = "http://s01.warserver.cz"           

getInfo = create_getInfo(WarserverCz)