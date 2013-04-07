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
# http://www.filefactory.com/file/ymxkmdud2o3/n/random.bin

import re

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.network.RequestFactory import getURL
from module.utils import parseFileSize


def getInfo(urls):
    file_info = list()
    list_ids = dict()

    # Create a dict id:url. Will be used to retrieve original url
    for url in urls:
        m = re.search(FilefactoryCom.__pattern__, url)
        list_ids[m.group('id')] = url

    # WARN: There could be a limit of urls for request
    post_data = {'func': 'links', 'links': '\n'.join(urls)}
    rep = getURL('http://www.filefactory.com/tool/links.php', post=post_data, decode=True)

    # Online links
    for m in re.finditer(
            r'innerText">\s*<h1 class="name">(?P<N>.+) \((?P<S>[\w.]+) (?P<U>\w+)\)</h1>\s*<p>http://www.filefactory.com/file/(?P<ID>\w+).*</p>\s*<p class="hidden size">',
            rep):
        file_info.append((m.group('N'), parseFileSize(m.group('S'), m.group('U')), 2, list_ids[m.group('ID')]))

    # Offline links
    for m in re.finditer(
            r'innerText">\s*<h1>(http://www.filefactory.com/file/(?P<ID>\w+)/)</h1>\s*<p>\1</p>\s*<p class="errorResponse">Error: file not found</p>',
            rep):
        file_info.append((list_ids[m.group('ID')], 0, 1, list_ids[m.group('ID')]))

    return file_info


class FilefactoryCom(SimpleHoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?filefactory\.com/file/(?P<id>[a-zA-Z0-9]+)"
    __version__ = "0.39"
    __description__ = """Filefactory.Com File Download Hoster"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def process(self, pyfile):
        if self.premium and (not self.SH_CHECK_TRAFFIC or self.checkTrafficLeft()):
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail("File too large for free download")
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 900, "All free slots are busy")

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
            self.retry(wait_time=15 * 60, reason='Parallel downloads')
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
            self.parseError('Unable to detect premium direct link')

        self.logDebug('DIRECT PREMIUM LINK: ' + url)
        self.download(url, disposition=True)
