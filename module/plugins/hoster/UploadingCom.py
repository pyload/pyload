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
from pycurl import HTTPHEADER
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp
from module.common.json_layer import json_loads

class UploadingCom(SimpleHoster):
    __name__ = "UploadingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>[\w\d]+)"
    __version__ = "0.32"
    __description__ = """Uploading.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de", "zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'<title>Download (?P<N>.*?) for free on uploading.com</title>'
    FILE_SIZE_PATTERN = r'<span>File size: (?P<S>.*?)</span>'
    FILE_OFFLINE_PATTERN = r'<h2.*?>The requested file is not found</h2>'
        
    def process(self, pyfile):
        # set lang to english
        self.req.cj.setCookie("uploading.com", "lang", "1")
        self.req.cj.setCookie("uploading.com", "language", "1")
        self.req.cj.setCookie("uploading.com", "setlang", "en")
        self.req.cj.setCookie("uploading.com", "_lang", "en")
        
        if not "/get/" in self.pyfile.url:
            self.pyfile.url = self.pyfile.url.replace("/files", "/files/get")
        
        self.html = self.load(pyfile.url, decode = True)
        self.file_info = self.getFileInfo()
        
        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()                   
    
    def handlePremium(self):
        postData = {'action': 'get_link',
                    'code': self.file_info['ID'],
                    'pass': 'undefined'}

        self.html = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html)
        if url:
            url = url.group(1).replace("\\/", "/")
            self.download(url)
        
        raise Exception("Plugin defect.")
    
    def handleFree(self):
        found = re.search('<h2>((Daily )?Download Limit)</h2>', self.html)
        if found:
            self.pyfile.error = found.group(1)
            self.logWarning(self.pyfile.error)
            self.retry(max_tries=6, wait_time = 21600 if found.group(2) else 900, reason = self.pyfile.error)  
        
        ajax_url = "http://uploading.com/files/get/?ajax"
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = self.pyfile.url
        
        response = json_loads(self.load(ajax_url, post = {'action': 'second_page', 'code': self.file_info['ID']}))        
        if 'answer' in response and 'wait_time' in response['answer']:
            wait_time = int(response['answer']['wait_time'])
            self.log.info("%s: Waiting %d seconds." % (self.__name__, wait_time))
            self.setWait(wait_time)
            self.wait()
        else:
            self.pluginParseError("AJAX/WAIT")
        
        response = json_loads(self.load(ajax_url, post = {'action': 'get_link', 'code': self.file_info['ID'], 'pass': 'false'}))
        if 'answer' in response and 'link' in response['answer']:
            url = response['answer']['link']
        else:
            self.pluginParseError("AJAX/URL")
            
        self.html = self.load(url)
        found = re.search(r'<form id="file_form" action="(.*?)"', self.html)
        if found:
            url = found.group(1)
        else:
            self.pluginParseError("URL")
        
        self.download(url)
        
        check = self.checkDownload({"html" : re.compile("\A<!DOCTYPE html PUBLIC")})
        if check == "html":
            self.logWarning("Redirected to a HTML page, wait 10 minutes and retry")
            self.setWait(600, True)
            self.wait()
        
getInfo = create_getInfo(UploadingCom)