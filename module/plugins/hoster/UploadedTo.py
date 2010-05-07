# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.Hoster import Hoster
import hashlib

class UploadedTo(Hoster):
    __name__ = "UploadedTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?u(?:p)?l(?:oaded)?\.to/(?:file/|\?id=)?(.+)"
    __version__ = "0.3"
    __description__ = """Uploaded.to Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.time_plus_wait = None	#time() + wait in seconds
        self.api_data = None
        self.want_reconnect = False
        self.read_config()
        self.account = None
        self.multi_dl = False
        self.usePremium = self.config['premium']
        if self.usePremium:
            self.account = self.parent.core.pluginManager.getAccountPlugin(self.__name__)
            req = self.account.getAccountRequest(self)
            if req:
                self.req = req
                self.multi_dl = True
                self.req.canContinue = True
            else:
                self.usePremium = False

        self.start_dl = False

    def prepare(self, thread):        
        self.want_reconnect = False
        tries = 0

        while not self.pyfile.status.url:
            self.download_html()

            self.pyfile.status.exists = self.file_exists()

            if not self.pyfile.status.exists:
                return False
                
            self.download_api_data()
            
            self.pyfile.status.filename = self.get_file_name()
            
            if self.usePremium:
                info = self.account.getAccountInfo(self.account.getAccountData(self)[0])
                self.logger.info(_("%s: Use Premium Account (%sGB left)") % (self.__name__, info["trafficleft"]/1024/1024))
                if self.api_data["size"] > info["trafficleft"]:
                    self.logger.info(_("%s: Not enough traffic left" % self.__name__))
                    self.usePremium = False
                else:
                    self.pyfile.status.url = self.parent.url
                    return True
                
            self.get_waiting_time()

            self.pyfile.status.waituntil = self.time_plus_wait
            self.pyfile.status.url = self.get_file_url()
            self.pyfile.status.want_reconnect = self.want_reconnect

            thread.wait(self.parent)

            self.pyfile.status.filename = self.get_file_name()

            tries += 1
            if tries > 5:
                raise Exception, "Error while preparing DL"
        return True
        
    def download_api_data(self):
        url = self.parent.url
        match = re.compile(self.__pattern__).search(url)
        if match:
            src = self.load("http://uploaded.to/api/file", cookies=False, get={"id": match.group(1).split("/")[0]})
            if not src.find("404 Not Found"):
                return
            self.api_data = {}
            lines = src.splitlines()
            self.api_data["filename"] = lines[0]
            self.api_data["size"] = int(lines[1]) # in kbytes
            self.api_data["checksum"] = lines[2] #sha1

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url, cookies=False)

    def get_waiting_time(self):
        try:
            wait_minutes = re.search(r"Or wait ([\d\-]+) minutes", self.html).group(1)
            if int(wait_minutes) < 0: wait_minutes = 1
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            self.time_plus_wait = 0

    def get_file_url(self):
        if self.usePremium:
            self.start_dl = True
            return self.parent.url
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
            return self.parent.url

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
    
    def proceed(self, url, location):
        if self.usePremium:
            self.load(url, cookies=True, just_header=True)
            if self.cleanUrl(self.req.lastEffectiveURL) == self.cleanUrl(url):
                self.logger.info(_("UploadedTo indirect download"))
                url = self.cleanUrl(url)+"?redirect"
            self.download(url, location, cookies=True)
        else:
            self.download(url, location, cookies=False, post={"download_submit": "Free Download"})

    def check_file(self, local_file):
        if self.api_data and self.api_data["checksum"]:
            h = hashlib.sha1()
            f = open(local_file, "rb")
            while True:
                data = f.read(128)
                if not data:
                    break
                h.update(data)
            f.close()
            hexd = h.hexdigest()
            if hexd == self.api_data["checksum"]:
                return (True, 0)
            else:
                return (False, 1)
        else:
            return (True, 5)
