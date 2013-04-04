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

# http://www.putlocker.com/file/83C174C844583CF7

import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class PutlockerCom(SimpleHoster):
    __name__ = "PutlockerCom"
    __type__ = "hoster"
    __pattern__ = r'http://(www\.)?putlocker\.com/(file|embed)/[A-Z0-9]+'
    __version__ = "0.22"
    __description__ = """Putlocker.Com"""
    __author_name__ = ("jeix", "stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_OFFLINE_PATTERN = r"This file doesn't exist, or has been removed."
    FILE_INFO_PATTERN = r'site-content">\s*<h1>(?P<N>.+)<strong>\( (?P<S>[^)]+) \)</strong></h1>'

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        self.link = self._getLink()
        if not self.link.startswith('http://'):
            self.link = "http://www.putlocker.com" + self.link
        self.download(self.link, disposition=True)

    def _getLink(self):
        self.hash = re.search("<input type=\"hidden\" value=\"([a-z0-9]+)\" name=\"hash\">", self.html)
        # if self.hash is None:
        # self.fail("%s: Plugin broken." % self.__name__)

        self.param = "hash=" + self.hash.group(1) + "&confirm=Continue+as+Free+User"
        self.html2 = self.load(self.pyfile.url, post=self.param)
        if ">You have exceeded the daily stream limit for your country\\. You can wait until tomorrow" in self.html2 or "(>This content server has been temporarily disabled for upgrades|Try again soon\\. You can still download it below\\.<)" in self.html2:
            self.waittime = 2 * 60 * 60
            self.retry(wait_time=self.waittime, reason="Waiting %s seconds" % self.waittime)

        self.link = re.search(
            "<a href=\"/gopro\\.php\">Tired of ads and waiting\\? Go Pro\\!</a>[\t\n\rn ]+</div>[\t\n\rn ]+<a href=\"(/.*?)\"",
            self.html2)
        if self.link is None:
            self.link = re.search("\"(/get_file\\.php\\?download=[A-Z0-9]+\\&key=[a-z0-9]+)\"", self.html2)

        if self.link is None:
            self.link = re.search("\"(/get_file\\.php\\?download=[A-Z0-9]+\\&key=[a-z0-9]+&original=1)\"", self.html2)

        if self.link is None:
            self.link = re.search("\"(/get_file\\.php\\?id=[A-Z0-9]+\\&key=[A-Za-z0-9=]+\\&original=1)\"", self.html2)

        if self.link is None:
            self.link = re.search("playlist: \\'(/get_file\\.php\\?stream=[A-Za-z0-9=]+)\\'", self.html2)
            if not self.link is None:
                self.html3 = self.load("http://www.putlocker.com" + self.link.group(1))
                self.link = re.search("media:content url=\"(http://.*?)\"", self.html3)
                if self.link is None:
                    self.link = re.search("\"(http://media\\-b\\d+\\.putlocker\\.com/download/\\d+/.*?)\"", self.html3)

                    # if link is None:
                    # self.fail("%s: Plugin broken." % self.__name__)

        return self.link.group(1).replace("&amp;", "&")
