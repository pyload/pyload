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
from module.common.json_layer import json_loads
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getURL

class IfileIt(SimpleHoster):
    __name__ = "IfileIt"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(?:ifile\.it|mihd\.net)/(\w+).*"
    __version__ = "0.24"
    __description__ = """Ifile.it"""
    __author_name__ = ("zoidberg")

    #EVAL_PATTERN = r'(eval\(function\(p,a,c,k,e,d\).*)'
    #DEC_PATTERN = r"requestBtn_clickEvent[^}]*url:\s*([^,]+)"
    DOWNLOAD_LINK_PATTERN = r'</span> If it doesn\'t, <a target="_blank" href="([^"]+)">'
    RECAPTCHA_KEY_PATTERN = r"var __recaptcha_public\s*=\s*'([^']+)';"
    FILE_INFO_PATTERN = r'<span style="cursor: default;[^>]*>\s*(?P<N>.*?)\s*&nbsp;\s*<strong>\s*(?P<S>[0-9.]+)\s*(?P<U>[kKMG])i?B\s*</strong>\s*</span>'
    FILE_OFFLINE_PATTERN = r'$\("#errorPnl"\)\.empty\(\)\.append\( "no such file" \);'
        
    def handleFree(self):      
        ukey = re.search(self.__pattern__, self.pyfile.url).group(1)
        json_url = 'http://ifile.it/download-request2.json?ukey=' + ukey
             
        json_response = json_loads(self.load(json_url))
        self.logDebug(json_response)
        if json_response["captcha"]:
            captcha_key = re.search(self.RECAPTCHA_KEY_PATTERN, self.html).group(1)
            recaptcha = ReCaptcha(self)

            for i in range(5):
                captcha_challenge, captcha_response = recaptcha.challenge(captcha_key)

                json_response = json_loads(self.load(json_url, post={
                    "ctype": "recaptcha",
                    "recaptcha_challenge": captcha_challenge,
                    "recaptcha_response": captcha_response
                }))

                self.logDebug(json_response)
                if json_response["retry"]:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
                    break
            else:
                self.fail("Incorrect captcha")

        # load twice
        self.html = self.load(self.pyfile.url)
        self.html = self.load(self.pyfile.url)
        download_url = re.search(self.DOWNLOAD_LINK_PATTERN, self.html).group(1)

        self.download(download_url)

getInfo = create_getInfo(IfileIt)