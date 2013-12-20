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

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilefactoryCom(SimpleHoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?filefactory\.com/file/(?P<id>[a-zA-Z0-9]+)"
    __version__ = "0.43"
    __description__ = """Filefactory.Com File Download Hoster"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<div id="file_name"[^>]*>\s*<h2>(?P<N>[^<]+)</h2>\s*<div id="file_info">(?P<S>[\d.]+) (?P<U>\w+) uploaded'
    DIRECT_LINK_PATTERN = r'<section id="downloadLink">\s*<p class="textAlignCenter">\s*<a href="([^"]+)">[^<]+</a>\s*</p>\s*</section>'

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail("File too large for free download")
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 15 * 60, "All free slots are busy")

        m = re.search(r'data-href-direct="(http://[^"]+)"', self.html)
        if m:
            self.setWait(30)
            self.wait()
            direct = m.group(1)
        else:  # This section could be completely useless now
            # Load the page that contains the direct link
            url = re.search(r"document\.location\.host \+\s*'(.+)';", self.html)
            if not url:
                self.parseError('Unable to detect free link')
            url = 'http://www.filefactory.com' + url.group(1)
            self.html = self.load(url, decode=True)

            # Free downloads wait time
            waittime = re.search(r'id="startWait" value="(\d+)"', self.html)
            if not waittime:
                self.parseError('Unable to detect wait time')
            self.setWait(int(waittime.group(1)))
            self.wait()

            # Parse the direct link and download it
            direct = re.search(r'data-href-direct="(.*)" class="button', self.html)
            if not direct:
                self.parseError('Unable to detect free direct link')
            direct = direct.group(1)

        self.logDebug('DIRECT LINK: ' + direct)
        self.download(direct, disposition=True)

        check = self.checkDownload({"multiple": "You are currently downloading too many files at once.",
                                    "error": '<div id="errorMessage">'})

        if check == "multiple":
            self.logDebug("Parallel downloads detected; waiting 15 minutes")
            self.retry(wait_time=15 * 60, reason="Parallel downloads")
        elif check == "error":
            self.fail("Unknown error")

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            url = header['location'].strip()
            if not url.startswith("http://"):
                url = "http://www.filefactory.com" + url
        elif 'content-disposition' in header:
            url = self.pyfile.url
        else:
            html = self.load(self.pyfile.url)
            found = re.search(self.DIRECT_LINK_PATTERN, html)
            if found:
                url = found.group(1)
            else:
                self.parseError('Unable to detect premium direct link')

        self.logDebug('DIRECT PREMIUM LINK: ' + url)
        self.download(url, disposition=True)


getInfo = create_getInfo(FilefactoryCom)
