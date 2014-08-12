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
"""

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class EasybytezCom(XFileSharingPro):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?easybytez.com/(\w+).*'
    __version__ = "0.17"
    __description__ = """Easybytez.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    HOSTER_NAME = "easybytez.com"

    FILE_INFO_PATTERN = r'<span class="name">(?P<N>.+)</span><br>\s*<span class="size">(?P<S>[^<]+)</span>'
    OFFLINE_PATTERN = r'<h1>File not available</h1>'

    LINK_PATTERN = r'(http://(\w+\.(easyload|easybytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/[^"<]+)'
    OVR_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    ERROR_PATTERN = r'(?:class=["\']err["\'][^>]*>|<Center><b>)(.*?)</'

    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


getInfo = create_getInfo(EasybytezCom)
