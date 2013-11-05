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

    @author: Walter Purcaro
"""

from module.plugins.hoster.PutlockerCom import PutlockerCom


class SockshareCom(PutlockerCom):
    __name__ = "SockshareCom"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?sockshare\.com/(mobile/)?(file|embed)/(?P<ID>[A-Z0-9]+)'
    __version__ = "0.01"
    __description__ = """Sockshare.Com"""
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.sockshare.com/file/\g<ID>')]
    HOSTER_NAME = "sockshare.com"
