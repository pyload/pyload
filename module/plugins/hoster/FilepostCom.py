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
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha
from module.common.json_layer import json_loads
from time import time

class FilepostCom(SimpleHoster):
    __name__ = "FilepostCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?filepost\.com/files/([^/]+).*"
    __version__ = "0.23"
    __description__ = """Filepost.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<h1>(?P<N>[^<]+)</h1>\s*<div class="ul">\s*<ul>\s*<li><span>Size:</span> (?P<S>[0-9.]+) (?P<U>[kKMG])i?B</li>'
    FILE_OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>'
    RECAPTCHA_KEY_PATTERN = r"Captcha.init\({\s*key:\s*'([^']+)'"
    FLP_TOKEN_PATTERN = r"store.set\('(?:flp_)?token', '([^']+)'\);"

    def handleFree(self):
        # Find token and captcha key
        file_id = re.search(self.__pattern__, self.pyfile.url).group(1)

        found = re.search(self.FLP_TOKEN_PATTERN, self.html)
        if not found: self.parseError("Token")
        flp_token = found.group(1)

        found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
        if not found: self.parseError("Captcha key")
        captcha_key = found.group(1)

        url = 'https://filepost.com/files/get/'

        # Get wait time
        get_dict = {'SID' : self.req.cj.getCookie('SID'), 'JsHttpRequest' : str(int(time()*10000)) + '-xml'}
        post_dict = {'action' : 'set_download', 'download' : flp_token, 'code' : file_id}
        json_response = json_loads(self.load(url, get = get_dict, post = post_dict))
        self.logDebug(json_response)
        try:
            self.setWait(int(json_response['js']['answer']['wait_time']))
        except Exception, e:
            self.logError(e)
            self.self.parseError("Wait time")
        self.wait()

        # Solve recaptcha
        recaptcha = ReCaptcha(self)
        for i in range(5):
            captcha_challenge, captcha_response = recaptcha.challenge(captcha_key)
            self.logDebug("RECAPTCHA: %s : %s : %s" % (captcha_key, captcha_challenge, captcha_response))

            get_dict['JsHttpRequest'] = str(int(time()*10000)) + '-xml'
            post_dict = {'download' : flp_token, 'code' : file_id,
                "recaptcha_challenge_field" : captcha_challenge,
                "recaptcha_response_field" : captcha_response
                }

            json_response = json_loads(self.load(url, get = get_dict, post = post_dict))
            try:
                download_url = json_response['js']['answer']['link']
                self.correctCaptcha()
                break
            except:
                self.invalidCaptcha()
        else: self.fail("Invalid captcha")

        # Download
        self.download(download_url)
        
getInfo = create_getInfo(FilepostCom)