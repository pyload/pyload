#!/usr/bin/env python
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

    @author: jeix
"""

import re

from time import time

from module.plugins.Hoster import Hoster

def timestamp():
    return int(time()*1000)

class UploadingCom(Hoster):
    __name__ = "UploadingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploading\.com/files/(?:get/)?[\w\d]+/?"
    __version__ = "0.2"
    __description__ = """Uploading.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de")
        
    def setup(self):
        self.html = [None,None,None]
        if self.account:
            self.resumeDownload = True
            self.multiDL = True
        else:
            self.resumeDownload = False
            self.multiDL = False

    def process(self, pyfile):
        # set lang to english
        self.req.cj.setCookie("uploading.com", "lang", "1")
        self.req.cj.setCookie("uploading.com", "language", "1")
        self.req.cj.setCookie("uploading.com", "setlang", "en")
        self.req.cj.setCookie("uploading.com", "_lang", "en")
        
        if not "/get" in self.pyfile.url:
            self.pyfile.url = self.pyfile.url.replace("/files", "/files/get")
        
        self.html[0] = self.load(self.pyfile.url)
        if re.search(r'<h2 style=".*?">The requested file is not found</h2>', self.html[0]) is not None:
            self.offline()
            
        self.pyfile.name = re.search(r'<title>Download (.*?) for free on uploading.com</title>', self.html[0]).group(1)
        
        if self.account:
            url = self.handlePremium()
        else:
            url = self.handleFree()
            
        self.download(url)
    
    def handlePremium(self):
        postData = {}
        postData['action'] = 'get_link'
        postData['code']   = re.search('code: "(.*?)",', self.html[0]).group(1)
        postData['pass']   = 'undefined'

        self.html[2] = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html[2])
        if url:
            return url.group(1).replace("\\/", "/")
        
        raise Exception("Plugin defect.")
    
    def handleFree(self):
        self.code   = re.search(r'name="code" value="(.*?)"', self.html[0]).group(1)
        self.fileid = re.search(r'name="file_id" value="(.*?)"', self.html[0]).group(1)
        
        postData = {}
        postData['action']  = 'second_page'
        postData['code']    = self.code
        postData['file_id'] = self.fileid
        
        self.html[1] = self.load(self.pyfile.url, post=postData)
        
        wait_time = re.search(r'timead_counter">(\d+)<', self.html[1])
        if not wait_time:
            wait_time = re.search(r'start_timer\((\d+)\)', self.html[1])
            
        if wait_time:
            wait_time = int(wait_time.group(1))
            self.log.info("%s: Waiting %d seconds." % (self.__name__, wait_time))
            self.setWait(wait_time)
            self.wait()
        
        
        postData = {}
        postData['action'] = 'get_link'
        postData['code']   = self.code
        postData['pass']   = 'undefined'
        
        if r'var captcha_src' in self.html[1]:
            captcha_url = "http://uploading.com/general/captcha/download%s/?ts=%d" % (self.fileid, timestamp())
            postData['captcha_code'] = self.decryptCaptcha(captcha_url)

        self.html[2] = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html[2])
        if url:
            return url.group(1).replace("\\/", "/")

        raise Exception("Plugin defect.")
