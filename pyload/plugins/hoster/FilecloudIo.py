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
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, PluginParseError
from module.common.json_layer import json_loads
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getURL

class FilecloudIo(SimpleHoster):
    __name__ = "FilecloudIo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(?:filecloud\.io|ifile\.it|mihd\.net)/(?P<ID>\w+).*"
    __version__ = "0.01"
    __description__ = """Filecloud.io (formerly Ifile.it) plugin - free account only"""
    __author_name__ = ("zoidberg")

    FILE_SIZE_PATTERN = r'{var __ab1 = (?P<S>\d+);}'
    FILE_NAME_PATTERN = r'id="aliasSpan">(?P<N>.*?)&nbsp;&nbsp;<'
    FILE_OFFLINE_PATTERN = r'l10n.(FILES__DOESNT_EXIST|REMOVED)'
    TEMP_OFFLINE_PATTERN = r'l10n.FILES__WARNING'
    
    UKEY_PATTERN = r"'ukey'\s*:'(\w+)',"
    AB1_PATTERN = r"if\( __ab1 == '(\w+)' \)"
    ERROR_MSG_PATTERN = r"var __error_msg\s*=\s*l10n\.(.*?);"
    DOWNLOAD_LINK_PATTERN = r'"(http://s\d+.filecloud.io/%s/\d+/.*?)"'
    RECAPTCHA_KEY_PATTERN = r"var __recaptcha_public\s*=\s*'([^']+)';"    
    RECAPTCHA_KEY = '6Lf5OdISAAAAAEZObLcx5Wlv4daMaASRov1ysDB1'
    
    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1
        
    def handleFree(self):
        data = {"ukey": self.file_info['ID']}
        
        found = re.search(self.AB1_PATTERN, self.html)
        if not found:
            raise PluginParseError("__AB1")
        data["__ab1"] = found.group(1)
    
        if not self.account:
            self.fail("User not logged in")
        elif not self.account.logged_in:
            recaptcha = ReCaptcha(self)
            captcha_challenge, captcha_response = recaptcha.challenge(self.RECAPTCHA_KEY)
            self.account.form_data = {"recaptcha_challenge_field" : captcha_challenge,
                                      "recaptcha_response_field" : captcha_response}
            self.account.relogin(self.user)
            self.retry(max_tries = 2)
                      
        json_url = "http://filecloud.io/download-request.json"
        response = self.load(json_url, post = data)
        self.logDebug(response)        
        response = json_loads(response)
        
        if "error" in response and response["error"]:
            self.fail(response)
        
        self.logDebug(response)
        if response["captcha"]:
            recaptcha = ReCaptcha(self)
            found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
            captcha_key = found.group(1) if found else self.RECAPTCHA_KEY
            data["ctype"] = "recaptcha"
            
            for i in range(5):
                data["recaptcha_challenge"], data["recaptcha_response"] = recaptcha.challenge(captcha_key)
                
                json_url = "http://filecloud.io/download-request.json"
                response = self.load(json_url, post = data)
                self.logDebug(response)
                response = json_loads(response)
                
                if "retry" in response and response["retry"]:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
                    break
            else:
                self.fail("Incorrect captcha")

        if response["dl"]:
            self.html = self.load('http://filecloud.io/download.html')
            found = re.search(self.DOWNLOAD_LINK_PATTERN % self.file_info['ID'], self.html)
            if not found:
                raise PluginParseError("Download URL")
            download_url = found.group(1)
            self.logDebug("Download URL: %s" % download_url)
            
            if "size" in self.file_info and self.file_info['size']:
                self.check_data = {"size": int(self.file_info['size'])}    
            self.download(download_url)
        else:
            self.fail("Unexpected server response")

getInfo = create_getInfo(FilecloudIo)