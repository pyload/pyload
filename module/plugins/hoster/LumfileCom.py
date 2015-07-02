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
from module.plugins.ReCaptcha import ReCaptcha


class LumfileCom(SimpleHoster):
    __name__ = "LumfileCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?lumfile\.com/(?P<id>[^/]+)/?.*"
    __version__ = "0.01"
    __description__ = """Lumfile.com hoster plugin"""
    __author_name__ = ("igelkun")
    __author_mail__ = ("ich.freak@gmx.net")

    FILE_NAME_PATTERN = r'File: <span>(?P<N>.+)</span>'
    FILE_SIZE_PATTERN = r'</span>\[(?P<S>[0-9.]+) (?P<U>.{,2})\]'
    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b>'

    #RECAPTCHA_KEY = '6LcSCtISAAAAABdiio55G1AhWe-dPNJjMZsjjLRg'
    CAPTCHA_KEY_PATTERN = r'http://www.google.com/recaptcha/api/challenge\?k=([^"]*)'

    POST_INFO_PATTERN = r'name="op" value="(?P<op>\w*)".*name="usr_login" value="(?P<login>\w*)".*name="id" value="(?P<id>\w*)".*name="fname" value="(?P<fname>[^"]*)".*name="referer" value="(?P<referer>[^"]*)"'
    POST_INFO_PATTERN2 = r'name="op" value="(?P<op>\w*)".*name="id" value="(?P<id>\w*)".*name="rand" value="(?P<rand>[^"]*)".*name="referer" value="(?P<referer>[^"]*)"'
    TEMP_OFFLINE_PATTERN = r'users with no account have the ability to download files at speeds not exceeding'
    NO_FREE_PATTERN = r'owner has limited free downloads'
    SECONDS_PATTERN = r'Wait <span id="[^"]*">([^<]*)</span> seconds'

    def handleFree(self):
        rand      = ''
        op        = re.search(r'name="op" value="([^"]*)"', self.html).group(1)
        usr_login = re.search(r'name="usr_login" value="([^"]*)"', self.html).group(1)
        usr_id    = re.search(r'name="id" value="([^"]*)"', self.html).group(1)
#        rand      = re.search(r'name="rand" value="([^"]*)"', self.html).group(1)
        fname    = re.search(r'name="fname" value="([^"]*)"', self.html).group(1)
        referer   = re.search(r'name="referer" value="([^"]*)"', self.html).group(1)

        self.logDebug("posting op="+op+" login="+usr_login+" id="+usr_id+" fname="+fname+" referer="+referer)
        m = re.search(self.POST_INFO_PATTERN, self.html)
        self.html = self.load(self.pyfile.url, post={'op':         op,
                                                     'usr_login':  usr_login,
                                                     'id' :        usr_id,
#                                                     'rand' :      rand,
                                                     'fname' :     fname,
                                                     'referer' :   referer,
                                                     'method_free':"Download slow speed"})

        if re.search(self.TEMP_OFFLINE_PATTERN, self.html):
          self.retry(wait_time=2*60*60, reason="Download limit exceeded")

        if re.search(self.NO_FREE_PATTERN, self.html):
          self.fail("not downloadable without accout")

        waittime = re.search(self.SECONDS_PATTERN, self.html).group(1)
        if waittime:
          self.setWait(waittime)
          self.wait()

        m = re.search(self.POST_INFO_PATTERN2, self.html)

        #handle captcha
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group(1)
        recaptcha = ReCaptcha(self) 
        challenge, response = recaptcha.challenge(captcha_key)
        post_data = {'op': m.group('op'),
                     'id': m.group('id'),
                     'rand': m.group('rand'),
                     'refered': m.group('referer'),
                     'method_free': 'Download slow speed',
                     'method_premium': '',
                     'recaptcha_challenge_field': challenge,
                     'recaptcha_response_field': response,
                     'down_script': 1,
                     'use_download_manager': 0}
        self.download(self.pyfile.url, post=post_data)
        check = self.checkDownload({"html": re.compile("\A<!DOCTYPE html PUBLIC")})
        if check == "html":
            self.logDebug("Wrong captcha entered")
            self.invalidCaptcha()
            self.retry()


getInfo = create_getInfo(LumfileCom)
