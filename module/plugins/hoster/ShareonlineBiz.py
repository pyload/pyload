#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from base64 import b64decode
import hashlib
import random
from time import sleep

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks

    
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
    __version__ = "0.22"
    __description__ = """Shareonline.biz Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

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
        
        self.html = self.load(self.pyfile.url) #refer, stuff
        self.html = self.load("%s/free/" % self.pyfile.url, post={"dl_free":"1", "choice": "free"})
        if re.search(r"/failure/full/1", self.req.lastEffectiveURL):
            self.setWait(120)
            self.log.info("%s: no free slots, waiting 120 seconds" % self.__name__)
            self.wait()
            self.retry(max_tries=60)
            
        if "Captcha number error or expired" in self.html:
            captcha = self.decryptCaptcha("http://www.share-online.biz/captcha.php", get={"rand":"0.%s" % random.randint(10**15,10**16)})
                
            self.log.debug("%s Captcha: %s" % (self.__name__, captcha))
            sleep(3)
            
            self.html = self.load(self.pyfile.url, post={"captchacode": captcha})
            
            if r"Der Download ist Ihnen zu langsam" not in self.html and r"The download is too slow for you" not in self.html:
                self.fail("Plugin defect. Save dumps and report.")

        if "Kein weiterer Download-Thread möglich!" in self.html: #TODO corresponding translation
            self.retry(wait_time=30, reason=_("Parallel download issue"))

        m = re.search("var wait=(\d+);", self.html[1])
        wait_time = int(m.group(1)) if m else 30
        self.setWait(wait_time)
        self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait_time))
        self.wait()
        
        file_url_pattern = r'var\sdl="(.*?)"'
        download_url = b64decode(re.search(file_url_pattern, self.html).group(1))
        
        self.download(download_url)

        check = self.checkDownload({"invalid" : "Dieses Download-Ticket ist ungültig!",
                                    "error"   : "Es ist ein unbekannter Fehler aufgetreten"})
        if check == "invalid":
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
