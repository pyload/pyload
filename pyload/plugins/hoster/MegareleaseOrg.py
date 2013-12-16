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


class MegareleaseOrg(XFileSharingPro):
    __name__ = "MegareleaseOrg"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?megarelease.org/\w{12}"
    __version__ = "0.01"
    __description__ = """Megarelease.Org hoster plugin"""
    __author_name__ = ("derek3x", "stickell")
    __author_mail__ = ("derek3x@vmail.me", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<font color="red">%s/(?P<N>.+)</font> \((?P<S>[^)]+)\)</font>' % __pattern__

    HOSTER_NAME = "megarelease.org"

getInfo = create_getInfo(MegareleaseOrg)
