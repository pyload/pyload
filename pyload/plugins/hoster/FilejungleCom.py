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

from module.plugins.hoster.FileserveCom import FileserveCom, checkFile
from module.plugins.Plugin import chunks

class FilejungleCom(FileserveCom):
    __name__ = "FilejungleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filejungle\.com/f/(?P<id>[^/]+).*"
    __version__ = "0.51"
    __description__ = """Filejungle.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    URLS = ['http://www.filejungle.com/f/', 'http://www.filejungle.com/check_links.php', 'http://www.filejungle.com/checkReCaptcha.php']
    LINKCHECK_TR = r'<li>\s*(<div class="col1">.*?)</li>'
    LINKCHECK_TD = r'<div class="(?:col )?col\d">(?:<[^>]*>|&nbsp;)*([^<]*)'
    
    LONG_WAIT_PATTERN = r'<h1>Please wait for (\d+) (\w+)\s*to download the next file\.</h1>'

def getInfo(urls):    
    for chunk in chunks(urls, 100): yield checkFile(FilejungleCom, chunk)  