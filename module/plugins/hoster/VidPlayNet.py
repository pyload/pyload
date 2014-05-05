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
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://vidplay.net/38lkev0h3jv0

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class VidPlayNet(XFileSharingPro):
    __name__ = "VidPlayNet"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?vidplay\.net/\w{12}'
    __version__ = "0.01"
    __description__ = """VidPlay.net hoster plugin"""
    __author_name__ = ("t4skforce")
    __author_mail__ = ("t4skforce1337[AT]gmail[DOT]com")

    HOSTER_NAME = "vidplay.net"

    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b><br>\s*<br>'
    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h2>(?P<N>[^<]+)</h2>'
    DIRECT_LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+)?(/d/|(?:/files)?/\d+/\w+/)[^"\'<&]+)' % HOSTER_NAME


getInfo = create_getInfo(VidPlayNet)