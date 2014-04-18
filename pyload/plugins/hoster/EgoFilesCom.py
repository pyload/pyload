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

# Test link (random.bin):
# http://egofiles.com/mOZfMI1WLZ6HBkGG/random.bin

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class EgoFilesCom(SimpleHoster):
    __name__ = "EgoFilesCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?egofiles.com/(\w+)'
    __version__ = "0.15"
    __description__ = """Egofiles.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_INFO_PATTERN = r'<div class="down-file">\s+(?P<N>[^\t]+)\s+<div class="file-properties">\s+(File size|Rozmiar): (?P<S>[\w.]+) (?P<U>\w+) \|'
    FILE_OFFLINE_PATTERN = r'(File size|Rozmiar): 0 KB'
    WAIT_TIME_PATTERN = r'For next free download you have to wait <strong>((?P<m>\d*)m)? ?((?P<s>\d+)s)?</strong>'
    DIRECT_LINK_PATTERN = r'<a href="(?P<link>[^"]+)">Download ></a>'
    RECAPTCHA_KEY = '6LeXatQSAAAAAHezcjXyWAni-4t302TeYe7_gfvX'

    def setup(self):
        # Set English language
        self.load("https://egofiles.com/ajax/lang.php?lang=en", just_header=True)

    def process(self, pyfile):
        if self.premium and (not self.SH_CHECK_TRAFFIC or self.checkTrafficLeft()):
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)
        self.getFileInfo()

        # Wait time between free downloads
        if 'For next free download you have to wait' in self.html:
            m = re.search(self.WAIT_TIME_PATTERN, self.html).groupdict('0')
            waittime = int(m['m']) * 60 + int(m['s'])
            self.wait(waittime, True)

        downloadURL = ''
        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            post_data = {'recaptcha_challenge_field': challenge,
                         'recaptcha_response_field': response}
            self.html = self.load(self.pyfile.url, post=post_data, decode=True)
            m = re.search(self.DIRECT_LINK_PATTERN, self.html)
            if not m:
                self.logInfo('Wrong captcha')
                self.invalidCaptcha()
            elif hasattr(m, 'group'):
                downloadURL = m.group('link')
                self.correctCaptcha()
                break
            else:
                self.fail('Unknown error - Plugin may be out of date')

        if not downloadURL:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.download(downloadURL, disposition=True)

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            self.logDebug('DIRECT LINK from header: ' + header['location'])
            self.download(header['location'])
        else:
            self.html = self.load(self.pyfile.url, decode=True)
            self.getFileInfo()
            m = re.search(r'<a href="(?P<link>[^"]+)">Download ></a>', self.html)
            if not m:
                self.parseError('Unable to detect direct download url')
            else:
                self.logDebug('DIRECT URL from html: ' + m.group('link'))
                self.download(m.group('link'), disposition=True)


getInfo = create_getInfo(EgoFilesCom)
