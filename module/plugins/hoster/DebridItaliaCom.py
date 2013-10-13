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

import re

from module.plugins.Hoster import Hoster


class DebridItaliaCom(Hoster):
    __name__ = "DebridItaliaCom"
    __version__ = "0.05"
    __type__ = "hoster"
    __pattern__ = r"https?://.*debriditalia\.com"
    __description__ = """Debriditalia.com hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "DebridItalia")
            self.fail("No DebridItalia account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            url = "http://debriditalia.com/linkgen2.php?xjxfun=convertiLink&xjxargs[]=S<![CDATA[%s]]>" % pyfile.url
            page = self.load(url)
            self.logDebug("XML data: %s" % page)

            if 'File not available' in page:
                self.fail('File not available')
            else:
                new_url = re.search(r'<a href="(?:[^"]+)">(?P<direct>[^<]+)</a>', page).group('direct')

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"empty": re.compile(r"^$")})

        if check == "empty":
            self.retry(5, 120, 'Empty file downloaded')
