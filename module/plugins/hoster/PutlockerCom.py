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

    @author: jeix
"""

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster
from os import rename


class PutlockerCom(SimpleHoster):
    __name__ = "PutlockerCom"
    __type__ = "hoster"
    __pattern__ = r'http://(www\.)?putlocker\.com/(file|embed)/[A-Z0-9]+'
    __version__ = "0.29"
    __description__ = """Putlocker.Com"""
    __author_name__ = ("jeix", "stickell", "Walter Purcaro")
    __author_mail__ = ("", "l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_OFFLINE_PATTERN = r'This file doesn\'t exist, or has been removed.'
    FILE_INFO_PATTERN = r'site-content">\s*<h1>(?P<N>.+)<strong>\( (?P<S>[^)]+) \)</strong></h1>'

    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def processName(self, name_old):
        name = self.pyfile.name
        if name <= name_old:
            return
        name_new = re.sub(r'\.[^.]+$', "", name_old) + name[len(name_old):]
        file = self.lastDownload
        self.pyfile.name = name_new
        rename(file, file.rsplit(name)[0] + name_new)
        self.logInfo("%(name)s renamed to %(newname)s" % {"name": name, "newname": name_new})

    def process(self, pyfile):
        pyfile.url = re.sub(r'http://putlocker\.com', r'http://www.putlocker.com', pyfile.url)
        self.req.setOption("timeout", 120)
        # Due to a 0.4.9 core bug self.load would keep previous cookies even if overridden by cookies parameter.
        # Workaround using getURL. Can be reverted in 0.5 as the cookies bug has been fixed.
        self.html = getURL(pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)
        self.getFileInfo()

        name = pyfile.name

        self.download(self._getLink(), disposition=True)

        self.processName(name)

    def _getLink(self):
        self.html = getURL(self.pyfile.url, decode=True)
        hash_data = re.search(r'<input type="hidden" value="([a-z0-9]+)" name="hash">', self.html)
        if not hash_data:
            self.parseError("Unable to detect hash")

        post_data = {"hash": hash_data.group(1), "confirm": "Continue+as+Free+User"}
        self.html = self.load(self.pyfile.url, post=post_data)
        if (">You have exceeded the daily stream limit for your country\\. You can wait until tomorrow" in self.html or
            "(>This content server has been temporarily disabled for upgrades|Try again soon\\. You can still download it below\\.<)" in self.html):
            self.retry(wait_time=2 * 3600, reason="Download limit exceeded or server disabled")

        patterns = (r'(/get_file\.php\?id=[A-Z0-9]+&key=[A-Za-z0-9=]+&original=1)',
                    r'(/get_file\.php\?download=[A-Z0-9]+&key=[a-z0-9]+)',
                    r'(/get_file\.php\?download=[A-Z0-9]+&key=[a-z0-9]+&original=1)',
                    r'<a href="/gopro\.php">Tired of ads and waiting\? Go Pro!</a>[\t\n\rn ]+</div>[\t\n\rn ]+<a href="(/.*?)"')
        for pattern in patterns:
            link = re.search(pattern, self.html)
            if link:
                break
        else:
            link = re.search(r"playlist: '(/get_file\.php\?stream=[A-Za-z0-9=]+)'", self.html)
            if link:
                self.html = self.load("http://www.putlocker.com" + link.group(1))
                link = re.search(r'media:content url="(http://.*?)"', self.html)
                if not link:
                    link = re.search("\"(http://media\\-b\\d+\\.putlocker\\.com/download/\\d+/.*?)\"", self.html)
            else:
                self.parseError("Unable to detect a download link")

        link = link.group(1).replace("&amp;", "&")
        return link if link.startswith("http://") else "http://www.putlocker.com" + link
