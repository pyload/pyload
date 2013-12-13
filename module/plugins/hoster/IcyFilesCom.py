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

    @author: godofdream
"""

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IcyFilesCom(DeadHoster):
    __name__ = "IcyFilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?icyfiles\.com/(.*)"
    __version__ = "0.06"
    __description__ = """IcyFiles.com plugin - free only"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")


getInfo = create_getInfo(IcyFilesCom)
