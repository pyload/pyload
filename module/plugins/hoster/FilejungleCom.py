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

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha

def getInfo(urls):
    yield [(url, 0, 1, url) for url in urls]

class FilejungleCom(SimpleHoster):
    __name__ = "FilejungleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filejungle\.com/f/([^/]+).*"
    __version__ = "0.24"
    __description__ = """Filejungle.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<div id="file_name">(?P<N>[^<]+) <span class="filename_normal">\((?P<S>[0-9.]+) (?P<U>[kKMG])i?B\)</span></div>'
    FILE_OFFLINE_PATTERN = r'(This file is no longer available.</h1>|class="error_msg_title"> Invalid or Deleted File. </div>)'
    RECAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey='([^']+)'"
    WAIT_TIME_PATTERN = r'<h1>Please wait for (\d+) seconds to download the next file\.</h1>'

    def handleFree(self):       
        self.fail("Hoster not longer available")
        
