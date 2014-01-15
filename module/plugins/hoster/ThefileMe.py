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


class ThefileMe(XFileSharingPro):
    __name__ = "ThefileMe"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?thefile\.me/\w{12}"
    __version__ = "0.01"
    __description__ = """Thefile.me hoster plugin"""
    __author_name__ = ("igel")
    __author_mail__ = ("")

    HOSTER_NAME = "thefile.me"


getInfo = create_getInfo(ThefileMe)
