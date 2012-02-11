#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from base64 import b64decode
import hashlib
import random
from time import time, sleep

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.ReCaptcha import ReCaptcha
    
def getInfo(urls):
    api_url_base = "http://api.share-online.biz/linkcheck.php"
    
    for chunk in chunks(urls, 90):
        api_param_file = {"links": "\n".join(x.replace("http://www.share-online.biz/dl/","").rstrip("/") for x in chunk)} #api only supports old style links
        src = getURL(api_url_base, post=api_param_file)
        result = []
        for i, res in enumerate(src.split("\n")):
            if not res:
                continue
            fields = res.split(";")
            
            if fields[1] == "OK":
                status = 2
            elif fields[1] in ("DELETED", "NOT FOUND"):
                status = 1
            else:
                status = 3
                
            result.append((fields[2], int(fields[3]), status, chunk[i]))
        yield result

class ShareonlineBiz(Hoster):
    __name__ = "ShareonlineBiz"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(share\-online\.biz|egoshare\.com)/(download.php\?id\=|dl/)[\w]+"
    __version__ = "0.23"
    __description__ = """Shareonline.biz Download Hoster"""
    __author_name__ = ("spoob", "mkaay", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de", "zoidberg@mujmail.cz")

    def setup(self):
        # range request not working?
        #  api supports resume, only one chunk
        #  website isn't supporting resuming in first place
        self.file_id = re.search(r"(id\=|/dl/)([a-zA-Z0-9]+)", self.pyfile.url).group(2)
        self.pyfile.url = "http://www.share-online.biz/dl/" + self.file_id

        self.multiDL = False
        self.chunkLimit = 1
        if self.account and self.account.isPremium(self.user):
            self.multiDL = True

    def process(self, pyfile):
        self.downloadAPIData()
        pyfile.name = self.api_data["filename"]
        pyfile.sync()
        
        if self.account and self.account.isPremium(self.user):
            self.handleAPIPremium()
            #self.handleWebsitePremium()
        else:
            self.handleFree()

    def downloadAPIData(self):
        api_url_base = "http://api.share-online.biz/linkcheck.php?md5=1"
        api_param_file = {"links": self.pyfile.url.replace("http://www.share-online.biz/dl/","")} #api only supports old style links
        src = self.load(api_url_base, cookies=False, post=api_param_file)
        
        fields = src.split(";")
        self.api_data = {"fileid": fields[0],
                         "status": fields[1]}
        if not self.api_data["status"] == "OK":
            self.offline()
        self.api_data["filename"] = fields[2]
        self.api_data["size"] = fields[3] # in bytes
        self.api_data["checksum"] = fields[4].strip().lower().replace("\n\n", "") # md5

    def handleFree(self):
        self.resumeDownload = False
        
        self.html = self.load(self.pyfile.url, cookies = True) #refer, stuff
        self.setWait(3)
        self.wait()
        
        self.html = self.load("%s/free/" % self.pyfile.url, post={"dl_free":"1", "choice": "free"}, cookies = True, ref = True)
        if re.search(r"/failure/full/1", self.req.lastEffectiveURL):
            self.setWait(120)
            self.log.info("%s: no free slots, waiting 120 seconds" % self.__name__)
            self.wait()
            self.retry(max_tries=60)
            
        found = re.search(r'var wait=(\d+);', self.html)                    
                
        recaptcha = ReCaptcha(self)
        for i in range(5):
            #found = re.search(r'var dl="(.*?)";', self.html)            
            #captcha = found.group(1).decode("base64").split('|')[-1]}                  
            challenge, response = recaptcha.challenge("6LdatrsSAAAAAHZrB70txiV5p-8Iv8BtVxlTtjKX")            
            self.setWait(int(found.group(1)) if found else 30)             
            response = self.load("%s/free/captcha/%d" % (self.pyfile.url, int(time() * 1000)), post = {
                'dl_free': '1',
                'recaptcha_challenge_field': challenge,
                'recaptcha_response_field': response})
            
            if not response == '0':
                break

        else: self.fail("No valid captcha solution received")
        
        download_url = response.decode("base64")
        self.logDebug(download_url)
        if not download_url.startswith("http://"):
            self.parseError("download url")
        
        self.wait()        
        self.download(download_url)

        check = self.checkDownload({"invalid" : re.compile("<strong>(This download ticket is.*?)</strong>"),
                                    "error"   : "Es ist ein unbekannter Fehler aufgetreten"})
        if check == "invalid":
            self.logError(self.lastCheck.group(1))
            self.retry(reason=_("Invalid download ticket"))
        elif check == "error":
            self.fail(reason=_("ShareOnline internal problems"))

    
    def handleAPIPremium(self): #should be working better
        self.resumeDownload = True

        info = self.account.getUserAPI(self.user, self.req)
        if info["dl"].lower() == "not_available":
            self.fail("DL API error")
        self.req.cj.setCookie("share-online.biz", "dl", info["dl"])
        
        
        src = self.load("http://api.share-online.biz/account.php?username=%s&password=%s&act=download&lid=%s" % (self.user, self.account.accounts[self.user]["password"], self.file_id), post={})
        dlinfo = {}
        for line in src.splitlines():
            key, value = line.split(": ")
            dlinfo[key.lower()] = value
        
        if not dlinfo["status"].lower() == "online":
            self.offline()
        
        dlLink = dlinfo["url"]
        if dlLink.startswith("/_dl.php"):
            self.log.debug("got invalid downloadlink, falling back")
            self.handleWebsitePremium()
        else:
            self.download(dlLink)
    
    def handleWebsitePremium(self): #seems to be buggy
        self.resumeDownload = False
        
        self.html = self.load(self.pyfile.url)
        if r"Die Nummer ist leider nicht richtig oder ausgelaufen!" in self.html:
            self.retry()
        
        try:
            download_url = re.search('loadfilelink\.decode\("(.*?)"\);', self.html, re.S).group(1)
        except:
            self.fail("Session issue")
        
        self.download(download_url)
    
    def checksum(self, local_file):
        if self.api_data and self.api_data["checksum"]:
            h = hashlib.md5()
            f = open(local_file, "rb")
            h.update(f.read())
            f.close()
            hexd = h.hexdigest()
            if hexd == self.api_data["checksum"]:
                return True, 0
            else:
                return False, 1
        else:
            return True, 5
