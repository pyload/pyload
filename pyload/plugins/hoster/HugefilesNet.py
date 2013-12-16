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

# Test links (random.bin):
# http://hugefiles.net/prthf9ya4w6s

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class HugefilesNet(XFileSharingPro):
    __name__ = "HugefilesNet"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?hugefiles\.net/\w{12}"
    __version__ = "0.01"
    __description__ = """Hugefiles.net hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    HOSTER_NAME = "hugefiles.net"

    FILE_SIZE_PATTERN = r'File Size:</span>\s*<span[^>]*>(?P<S>[^<]+)</span></div>'


getInfo = create_getInfo(HugefilesNet)
