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
from pycurl import HTTPHEADER
from random import random

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads
from module.plugins.ReCaptcha import ReCaptcha

class AdsCaptcha():
    def __init__(self, plugin):
        self.plugin = plugin
    
    def challenge(self, src):
        js = self.plugin.req.load(src, cookies=True)
        
        try:
            challenge = re.search("challenge: '(.*?)',", js).group(1)
            server = re.search("server: '(.*?)',", js).group(1)
        except:
            self.plugin.fail("adscaptcha error")
        result = self.result(server,challenge)
        
        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%sChallenge.aspx" % server, get={"cid": challenge, "dummy": random()}, cookies=True, imgtype="jpg")

class RapidgatorNet(SimpleHoster):
    __name__ = "RapidgatorNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?(rapidgator.net)/file/(\d+)"
    __version__ = "0.04"
    __description__ = """rapidgator.net"""
    __author_name__ = ("zoidberg")
  
    FILE_INFO_PATTERN = r'Downloading:(\s*<[^>]*>)*\s*(?P<N>.*?)(\s*<[^>]*>)*\s*File size:\s*<strong>(?P<S>.*?)</strong>'
    FILE_OFFLINE_PATTERN = r'<title>File not found</title>'
    
    JSVARS_PATTERN = r"\s+var\s*(startTimerUrl|getDownloadUrl|captchaUrl|fid|secs)\s*=\s*'?(.*?)'?;" 
    DOWNLOAD_LINK_PATTERN = r"location.href = '(.*?)'"
    RECAPTCHA_KEY_PATTERN = r'"http://api.recaptcha.net/challenge?k=(.*?)"'
    ADSCAPTCHA_SRC_PATTERN = r'(http://api.adscaptcha.com/Get.aspx[^"\']*)'
        
    def handleFree(self):
        if "You can download files up to 500 MB in free mode" in self.html:
            self.fail("File too large for free download")
        
        self.checkWait()  
    
        jsvars = dict(re.findall(self.JSVARS_PATTERN, self.html))
        self.logDebug(jsvars)
        
        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        
        url = "http://rapidgator.net%s?fid=%s" % (jsvars.get('startTimerUrl', '/download/AjaxStartTimer'), jsvars["fid"])        
        jsvars.update(self.getJsonResponse(url))
        
        self.setWait(int(jsvars.get('secs', 30)) + 1, False)
        self.wait()
        
        url = "http://rapidgator.net%s?sid=%s" % (jsvars.get('getDownloadUrl', '/download/AjaxGetDownload'), jsvars["sid"])
        jsvars.update(self.getJsonResponse(url))
        
        self.req.http.lastURL = self.pyfile.url
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With:"])
        
        url = "http://rapidgator.net%s" % jsvars.get('captchaUrl', '/download/captcha')
        self.html = self.load(url)
        
        found = re.search(self.ADSCAPTCHA_SRC_PATTERN, self.html)
        if found:
            captcha_key = found.group(1)
            captcha = AdsCaptcha(self)
        else:
            found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
            if found:
                captcha_key = found.group(1)
                captcha = ReCaptcha(self)
                
            else:
                self.parseError("CAPTCHA")
        captcha_prov = captcha.__class__.__name__.lower()        
        
        for i in range(5):
            self.checkWait()
            captcha_challenge, captcha_response = captcha.challenge(captcha_key)

            self.html = self.load(url, post={
                "DownloadCaptchaForm[captcha]": "",
                "%s_challenge_field" % captcha_prov: captcha_challenge,
                "%s_response_field" % captcha_prov: captcha_response
            })

            if 'The verification code is incorrect' in self.html:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else:
            self.fail("No valid captcha solution received")
            
        found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
        if not found:
            self.parseError("download link")
        download_url = found.group(1)
        self.logDebug(download_url)
        self.download(download_url)
    
    def checkWait(self):
        found = re.search(r"(?:Delay between downloads must be not less than|Try again in)\s*(\d+)\s*(hour|minute)", self.html)
        if found:
            wait_time = int(found.group(1)) * {"h": 60, "m": 1}[found.group(2)]
        else:
            found = re.search(r"You have reached your (daily|hourly) downloads limit", self.html)
            if found:
                wait_time = 60
            else:
                return
        
        self.logDebug("Waiting %d minutes" % wait_time)
        self.setWait(wait_time * 60, True)
        self.wait()
        self.retry(max_tries = 24)
    
    def getJsonResponse(self, url):
        response = self.load(url, decode = True)
        if not response.startswith('{'):
            self.retry()        
        self.logDebug(url, response)
        return json_loads(response)        

getInfo = create_getInfo(RapidgatorNet)