# -*- coding: utf-8 -*-
###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class UptoboxCom(XFileSharingPro):
    __name__ = "UptoboxCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?uptobox\.com/\w+'
    __version__ = "0.08"
    __description__ = """Uptobox.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "uptobox.com"

    FILE_INFO_PATTERN = r'"para_title">(?P<N>.+) \((?P<S>[\d\.]+) (?P<U>\w+)\)'
    FILE_OFFLINE_PATTERN = r'>(File not found|Access Denied|404 Not Found)'
    TEMP_OFFLINE_PATTERN = r'>This server is in maintenance mode'

    WAIT_PATTERN = r'>(\d+)</span> seconds<'

    DIRECT_LINK_PATTERN = r'"(https?://\w+\.uptobox\.com/d/.*?)"'


getInfo = create_getInfo(UptoboxCom)
