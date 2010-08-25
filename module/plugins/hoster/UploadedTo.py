# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.Hoster import Hoster
from module.network.Request import getURL
import hashlib

def getInfo(urls):
    for url in urls:
        match = re.compile(UploadedTo.__pattern__).search(url)
        if match:
            src = getURL("http://uploaded.to/api/file", get={"id": match.group(1).split("/")[0]})
            if src.find("404 Not Found") >= 0:
                result.append((url, 0, 1, url))
                continue
            lines = src.splitlines()
            result.append((lines[0], int(lines[1]), 2, url))

class UploadedTo(Hoster):
    __name__ = "UploadedTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?u(?:p)?l(?:oaded)?\.to/(?:file/|\?id=)?(.+)"
    __version__ = "0.4"
    __description__ = """Uploaded.to Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    
    def setup(self):
        self.html = None
        self.api_data = None
        self.multiDL = False
        if self.account:
            self.multiDL = True
            self.req.canContinue = True
        
    def process(self, pyfile):
        self.url = False
        self.pyfile = pyfile
        self.prepare()
        self.proceed()
                
    
    def getInfo(self):
        self.download_api_data()
        self.pyfile.name = self.api_data["filename"]
        self.pyfile.sync()

    def prepare(self):        
        tries = 0

        while not self.url:
            self.download_html()

            if not self.file_exists():
                self.offline()
                
            self.download_api_data()
            
            # self.pyfile.name = self.get_file_name()
            
            if self.account:
                info = self.account.getAccountInfo(self.account.getAccountData(self)[0])
                self.log.debug(_("%s: Use Premium Account (%sGB left)") % (self.__name__, info["trafficleft"]/1024/1024))
                if self.api_data["size"]/1024 > info["trafficleft"]:
                    self.log.info(_("%s: Not enough traffic left" % self.__name__))
                    self.resetAcount()
                else:
                    self.url = self.get_file_url()
                    self.pyfile.name = self.get_file_name()
                    return True
                
            self.url = self.get_file_url()
            
            self.setWait(self.get_waiting_time())
            self.wait()

            self.pyfile.name = self.get_file_name()

            tries += 1
            if tries > 5:
                self.fail("Error while preparing DL")
        return True
        
    def download_api_data(self, force=False):
        if self.api_data and not force:
            return
        match = re.compile(self.__pattern__).search(self.pyfile.url)
        if match:
            src = self.load("http://uploaded.to/api/file", cookies=False, get={"id": match.group(1).split("/")[0]})
            if not src.find("404 Not Found"):
                return
            self.api_data = {}
            lines = src.splitlines()
            self.api_data["filename"] = lines[0]
            self.api_data["size"] = int(lines[1]) # in bytes
            self.api_data["checksum"] = lines[2] #sha1

    def download_html(self):
        self.html = self.load(self.pyfile.url, cookies=False)

    def get_waiting_time(self):
        try:
            wait_minutes = re.search(r"Or wait ([\d\-]+) minutes", self.html).group(1)
            if int(wait_minutes) < 0: wait_minutes = 1            
            self.wantReconnect = True
            return 60 * int(wait_minutes)
        except:
            return 0

    def get_file_url(self):
        if self.account:
            self.start_dl = True
            return self.cleanUrl(self.pyfile.url)
        try:
            file_url_pattern = r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">"
            return re.search(file_url_pattern, self.html).group(1)
        except:
            return None

    def get_file_name(self):
        try:
            if self.api_data and self.api_data["filename"]:
                return self.api_data["filename"]
            file_name = re.search(r"<td><b>\s+(.+)\s", self.html).group(1)
            file_suffix = re.search(r"</td><td>(\..+)</td></tr>", self.html)
            if not file_suffix:
                return file_name
            return file_name + file_suffix.group(1)
        except:
            return self.pyfile.url.split('/')[-1]

    def file_exists(self):
        if re.search(r"(File doesn't exist)", self.html) != None:
            return False
        else:
            return True
    
    def cleanUrl(self, url):
        url = url.replace("ul.to/", "uploaded.to/file/")
        url = url.replace("/?id=", "/file/")
        url = url.replace("?id=", "file/")
        url = re.sub("/\?(.*?)&id=", "/file/", url, 1)
        return url
    
    def proceed(self):
        if self.account:
            self.download(self.url+"?redirect", cookies=True)
        else:
            self.download(self.url, cookies=False, post={"download_submit": "Free Download"})
