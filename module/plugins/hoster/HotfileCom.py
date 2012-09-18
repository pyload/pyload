#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.RequestFactory import getURL
from module.utils import chunks

def getInfo(urls):
    api_url_base = "http://api.hotfile.com/"
    
    for chunk in chunks(urls, 90):
        api_param_file = {"action":"checklinks","links": ",".join(chunk),"fields":"id,status,name,size"} #api only supports old style links
        src = getURL(api_url_base, post=api_param_file)
        result = []
        for i, res in enumerate(src.split("\n")):
            if not res:
                continue
            fields = res.split(",")
            
            if fields[1] in ("1", "2"):
                status = 2
            else:
                status = 1
                
            result.append((fields[2], int(fields[3]), status, chunk[i]))
        yield result

class HotfileCom(Hoster):
    __name__ = "HotfileCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www.)?hotfile\.com/dl/\d+/[0-9a-zA-Z]+/"
    __version__ = "0.34"
    __description__ = """Hotfile.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay","JoKoT3")
    __author_mail__ = ("sitacuisses@yhoo.de","spoob@pyload.org","mkaay@mkaay.de","jokot3@gmail.com")

    FILE_OFFLINE_PATTERN = r'File is removed'

    def setup(self):
        self.html = [None, None]
        self.wantReconnect = False
        self.htmlwithlink = None
        self.url = None
        
        if self.premium:
            self.multiDL = True
            self.resumeDownload = True
            self.chunkLimit = -1
        else:
            self.multiDL = False
            self.chunkLimit = 1
    
    def apiCall(self, method, post, login=False):
        if not self.account and login:
            return
        elif self.account and login:
            return self.account.apiCall(method, post, self.user)
        post.update({"action": method})
        return self.load("http://api.hotfile.com/", post=post, decode=True)
        
    def process(self, pyfile):
        self.wantReconnect = False
        
        args = {"links":self.pyfile.url, "fields":"id,status,name,size,sha1"}
        resp = self.apiCall("checklinks", args)
        self.apiData = {}
        for k, v in zip(args["fields"].split(","), resp.strip().split(",")):
            self.apiData[k] = v
        
        if self.apiData["status"] == "0":
            self.offline()

        pyfile.name = self.apiData["name"]
        
        if not self.premium:
            self.downloadHTML()

            if self.FILE_OFFLINE_PATTERN in self.html[0]:
                self.offline()

            self.setWait(self.getWaitTime())
            self.wait()
            
            self.freeDownload()
        else:
            dl = self.account.apiCall("getdirectdownloadlink", {"link":self.pyfile.url}, self.user)
            #dl = unquote(dl).strip()  <- Made problems
            dl = dl.strip()
            self.download(dl)

    def downloadHTML(self):
        self.html[0] = self.load(self.pyfile.url, get={"lang":"en"})

    def freeDownload(self):
        
        form_content = re.search(r"<form style=.*(\n<.*>\s*)*?[\n\t]?<tr>", self.html[0])
        if form_content is None:
            print self.html[0]
            self.fail("Form not found in HTML. Can not proceed.")

        form_content = form_content.group(0)
        form_posts = dict(re.findall(r"<input\stype=hidden\sname=(\S*)\svalue=(\S*)>", form_content))
        
        self.html[1] = self.load(self.pyfile.url, post=form_posts)

        challenge = re.search(r"http://api\.recaptcha\.net/challenge\?k=([0-9A-Za-z]+)", self.html[1])
        
        if challenge:
            re_captcha = ReCaptcha(self)
            challenge, result = re_captcha.challenge(challenge.group(1))
            
            url = re.search(r'<form action="(/dl/[^"]+)', self.html[1] )
                        
            self.html[1] = self.load("http://hotfile.com"+url.group(1), post={"action": "checkcaptcha",
                                             "recaptcha_challenge_field" : challenge,
                                             "recaptcha_response_field": result})
            
            if "Wrong Code. Please try again." in self.html[1]:
                self.freeDownload()
                return
        
        file_url = re.search(r'a href="(http://hotfile\.com/get/\S*)"', self.html[1]).group(1)
        self.download(file_url)
          
    def getWaitTime(self):
        free_limit_pattern = re.compile(r"timerend=d\.getTime\(\)\+(\d+);")
        matches = free_limit_pattern.findall(self.html[0])
        if matches:
            wait_time = (sum([int(match) for match in matches])/1000) or 60
            if wait_time > 300: 
                self.wantReconnect = True
            return wait_time + 1
        else:
            self.fail("Don't know how long to wait. Cannot proceed.")