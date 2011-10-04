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

from module.common.json_layer import json_loads
from module.common.JsEngine import JsEngine
from module.plugins.ReCaptcha import ReCaptcha
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url, decode=True)
        if re.search(IfileIt.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(IfileIt.FILE_INFO_PATTERN, html)
            if found is not None:
                name, size, units = found.groups()
                size = float(size) * 1024 ** {'kB': 1, 'MB': 2, 'GB': 3}[units]
                result.append((name, size, 2, url))
    yield result


class IfileIt(Hoster):
    __name__ = "IfileIt"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*ifile\.it/.*"
    __version__ = "0.2"
    __description__ = """Ifile.it"""
    __author_name__ = ("zoidberg")

    EVAL_PATTERN = r'(eval\(function\(p,a,c,k,e,d\).*)'
    DEC_PATTERN = r"function requestBtn_clickEvent[^}]*url:\s*([^,]+)"
    DOWNLOAD_LINK_PATTERN = r'</span> If it doesn\'t, <a target="_blank" href="([^"]+)">'
    RECAPTCHA_KEY_PATTERN = r"var __recaptcha_public\s*=\s*'([^']+)';"
    FILE_INFO_PATTERN = r'<span style="cursor: default;[^>]*>\s*(.*?)\s*&nbsp;\s*<strong>\s*([0-9.]+)\s*(kB|MB|GB)\s*</strong>\s*</span>'
    FILE_OFFLINE_PATTERN = r'$\("#errorPnl"\)\.empty\(\)\.append\( "no such file" \);'

    def process(self, pyfile):
        self.html = self.load(pyfile.url)

        found = re.search(self.FILE_INFO_PATTERN, self.html)
        pyfile.name = found.group(1)
        pyfile.size = pyfile.size = float(found.group(2)) * 1024 ** {'kB': 1, 'MB': 2, 'GB': 3}[found.group(3)]

        eval_string = re.search(self.EVAL_PATTERN, self.html).group(1)
        dec_string = re.search(self.DEC_PATTERN, self.html).group(1)

        js = JsEngine()
        json_url = js.eval(eval_string + ";" + dec_string)
        self.logDebug(json_url)

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
        self.html = self.load(pyfile.url)
        self.html = self.load(pyfile.url)
        download_url = re.search(self.DOWNLOAD_LINK_PATTERN, self.html).group(1)

        self.download(download_url)