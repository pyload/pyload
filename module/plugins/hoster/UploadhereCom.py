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

from module.plugins.internal.DeadHoster import DeadHoster as UploadkingCom, create_getInfo
#from module.plugins.internal.SimpleHoster import create_getInfo
#from UploadkingCom import UploadkingCom

class UploadhereCom(UploadkingCom):
    __name__ = "UploadhereCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadhere\.com/\w{10}"
    __version__ = "0.12"
    __description__ = """Uploadhere.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    # shares code with UploadkingCom

create_getInfo(UploadhereCom)