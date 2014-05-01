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

    @author: t4skforce
"""

# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://epicshare.net/fch3m2bk6ihp/BigBuckBunny_320x180.mp4.html

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class EpicShareNet(XFileSharingPro):
    __name__ = "EpicShareNet"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?epicshare\.net/\w{12}'
    __version__ = "0.01"
    __description__ = """EpicShare.net hoster plugin"""
    __author_name__ = ("t4skforce")
    __author_mail__ = ("t4skforce1337[AT]gmail[DOT]com")

    HOSTER_NAME = "epicshare.net"

    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b><br><br>'
    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h2>(?P<N>[^<]+)</h2>'


getInfo = create_getInfo(EpicShareNet)