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

    @author: 4Christopher
"""

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class XvidstageCom(XFileSharingPro):
    __name__ = 'XvidstageCom'
    __version__ = '0.5'
    __pattern__ = r'http://(?:www.)?xvidstage.com/(?P<id>[0-9A-Za-z]+)'
    __type__ = 'hoster'
    __description__ = """A Plugin that allows you to download files from http://xvidstage.com"""
    __author_name__ = ('4Christopher')
    __author_mail__ = ('4Christopher@gmx.de')

    HOSTER_NAME = "xvidstage.com"

    def setup(self):
        self.resumeDownload = self.multiDL = self.premium

getInfo = create_getInfo(XvidstageCom)
