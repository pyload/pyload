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
# test.bin - 214 B - http://pandapla.net/pew1cz3ot586
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://pandapla.net/tz0rgjfyyoh7

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class PandaPlanet(XFileSharingPro):
    __name__ = "PandaPlanet"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?pandapla\.net/\w{12}'
    __version__ = "0.01"
    __description__ = """Pandapla.net hoster plugin"""
    __author_name__ = ("t4skforce")
    __author_mail__ = ("t4skforce1337[AT]gmail[DOT]com")

    HOSTER_NAME = "pandapla.net"

    FILE_SIZE_PATTERN = r'File Size:</b>\s*</td>\s*<td[^>]*>(?P<S>[^<]+)</td>\s*</tr>'
    FILE_NAME_PATTERN = r'File Name:</b>\s*</td>\s*<td[^>]*>(?P<N>[^<]+)</td>\s*</tr>'
    DIRECT_LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+)?(/d/|(?:/files)?/\d+/\w+/)[^"\'<]+\/(?!video\.mp4)[^"\'<]+)' % HOSTER_NAME


getInfo = create_getInfo(PandaPlanet)