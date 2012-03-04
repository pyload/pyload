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
from module.plugins.ReCaptcha import ReCaptcha as _ReCaptcha
    
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

#suppress ocr plugin
class ReCaptcha(_ReCaptcha):
    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%simage"%server, get={"c":challenge}, cookies=True, forceUser=True, imgtype="jpg")

class ShareonlineBiz(Hoster):
    __name__ = "ShareonlineBiz"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(share\-online\.biz|egoshare\.com)/(download.php\?id\=|dl/)[\w]+"
    __version__ = "0.25"
    __description__ = """Shareonline.biz Download Hoster"""
    __author_name__ = ("spoob", "mkaay", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de", "zoidberg@mujmail.cz")

    def setup(self):
        # range request not working?
        #  api supports resume, only one chunk
        #  website isn't supporting resuming in first place
        self.file_id = re.search(r"(id\=|/dl/)([a-zA-Z0-9]+)", self.pyfile.url).group(2)
        self.pyfile.url = "http://www.share-online.biz/dl/" + self.file_id

        self.resumeDownload = self.multiDL = self.premium
        self.chunkLimit = 1

    def process(self, pyfile):       
        if self.premium:
            self.handleAPIPremium()
            #web-download fallback removed - didn't work anyway
        else:
            self.handleFree()
            
        check = self.checkDownload({"invalid" : re.compile("<strong>(This download ticket is.*?)</strong>"),
                                    "error"   : "Es ist ein unbekannter Fehler aufgetreten"})
        if check == "invalid":
            self.logError(self.lastCheck.group(1))
            if self.premium: self.account.relogin()
            self.retry(reason=_("Invalid download ticket"))
        elif check == "error":
            self.fail(reason=_("ShareOnline internal problems"))

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
        self.api_data["md5"] = fields[4].strip().lower().replace("\n\n", "") # md5

    def handleFree(self):       
        self.downloadAPIData()
        self.pyfile.name = self.api_data["filename"]
        self.pyfile.size = self.api_data["size"]
        
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
    
    def handleAPIPremium(self): #should be working better                        
        src = self.load("http://api.share-online.biz/account.php?username=%s&password=%s&act=download&lid=%s" % (self.user, self.account.accounts[self.user]["password"], self.file_id), post={})
        self.api_data = dlinfo = {}
        for line in src.splitlines():
            key, value = line.split(": ")
            dlinfo[key.lower()] = value
        
        self.logDebug(dlinfo)
        if not dlinfo["status"] == "online":
            self.offline()
        
        self.pyfile.name = dlinfo["name"]
        self.pyfile.size = dlinfo["size"]
               
        dlLink = dlinfo["url"]
        if dlLink == "server_under_maintenance":
            self.tempoffline()
        else:
            self.download(dlLink)
    
    def checksum(self, local_file):
        if self.api_data and "md5" in self.api_data and self.api_data["md5"]:
            h = hashlib.md5()
            f = open(local_file, "rb")
            h.update(f.read())
            f.close()
            hexd = h.hexdigest()
            if hexd == self.api_data["md5"]:
                return True, 0
            else:
                return False, 1
        else:
            self.logWarning("MD5 checksum missing")
            return True, 5
