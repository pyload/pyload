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

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class HundredEightyUploadCom(XFileSharingPro):
    __name__ = "HundredEightyUploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?180upload\.com/(\w+).*"
    __version__ = "0.01"
    __description__ = """180upload.com hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.+)</td></tr>-->'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.]+) (?P<U>[A-Z]+)\s*<small>'

    HOSTER_NAME = "180upload.com"


getInfo = create_getInfo(HundredEightyUploadCom)
