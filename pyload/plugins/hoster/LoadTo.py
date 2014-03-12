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
# http://www.load.to/JWydcofUY6/random.bin
# http://www.load.to/oeSmrfkXE/random100.bin

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class LoadTo(SimpleHoster):
    __name__ = "LoadTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?load\.to/\w+"
    __version__ = "0.13"
    __description__ = """Load.to hoster plugin"""
    __author_name__ = ("halfman", "stickell")
    __author_mail__ = ("Pulpan3@gmail.com", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<a [^>]+>(?P<N>.+)</a></h3>\s*Size: (?P<S>\d+) (?P<U>[kKmMgG]?i?[bB])'
    URL_PATTERN = r'<form method="post" action="(.+?)"'
    FILE_OFFLINE_PATTERN = r'Can\'t find file. Please check URL.'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'
    RECAPTCHA_PATTERN = r'http://www.google.com/recaptcha/api/challenge'
    RECAPTCHA_KEY = "6Lc34eISAAAAAKNbPVyxBgNriTjPRmF-FA1oxApG"

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()

        # Check if File is online
        if re.search(self.FILE_OFFLINE_PATTERN, self.html):
            self.offline()

        # Search for Download URL
        m = re.search(self.URL_PATTERN, self.html)
        if not m:
            self.parseError('Unable to detect download URL')
        download_url = m.group(1)

        # Set Timer - may be obsolete
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1))

        # Check if reCaptcha is present
        m = re.search(self.RECAPTCHA_PATTERN, self.html)
        if not m:  # No captcha found
            self.download(download_url)
        else:
            recaptcha = ReCaptcha(self)
            for _ in xrange(5):
                challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
                if not response == '0':
                    break
            else:
                self.fail("No valid captcha solution received")

            self.download(download_url,
                          post={'recaptcha_challenge_field': challenge, 'recaptcha_response_field': response})

            # Verifiy reCaptcha by checking content of file for html 404-error
            check = self.checkDownload({"404": re.compile("\A<h1>404 Not Found</h1>")})
            if check == "404":
                self.logWarning("The captcha you entered was incorrect. Please try again.")
                self.invalidCaptcha()
                self.retry()


getInfo = create_getInfo(LoadTo)
