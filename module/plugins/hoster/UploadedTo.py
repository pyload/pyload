# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.ReCaptcha import ReCaptcha

def getInfo(urls):
    pattern = re.compile(UploadedTo.__pattern__)
    for chunk in chunks(urls, 10):
        result = []
        for url in chunk:
            match = pattern.search(url)
            if match:
                src = getURL("http://uploaded.to/api/file", get={"id": match.group(1).split("/")[0]}).decode("utf8", "ignore")
                if src.find("404 Not Found") >= 0:
                    result.append((url, 0, 1, url))
                    continue
                lines = src.splitlines()
                result.append((lines[0], int(lines[1]), 2, url))
        yield result

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
        self.url = False
        if self.account:
            self.multiDL = True
            self.chunkLimit = -1
            self.resumeDownload = True
        

    def process(self, pyfile):
        self.download_html()

        if not self.file_exists():
            self.offline()

        self.download_api_data()

        # self.pyfile.name = self.get_file_name()

        if self.account:
            info = self.account.getAccountInfo(self.user, True)
            self.log.debug(_("%(name)s: Use Premium Account (%(left)sGB left)") % {"name" :self.__name__, "left" : info["trafficleft"]/1024/1024})
            if self.api_data["size"]/1024 > info["trafficleft"]:
                self.log.info(_("%s: Not enough traffic left" % self.__name__))
                self.account.empty()
                self.resetAccount()
                self.fail(_("Traffic exceeded"))
            else:
                self.url = self.get_file_url()
                pyfile.name = self.get_file_name()
                self.download(self.url+"?redirect", cookies=True)

            return True


        self.url = self.get_file_url()

        wait = self.get_waiting_time()
        if wait:
            self.setWait(wait, True)
            self.wait()
            self.process(pyfile)
            return
        else:
            self.setWait(30, False)

        time = re.search(r'name="time" value="([^"]+)', self.html).group(1)
        time_secure = re.search(r'name="time_secure" value="([^"]+)', self.html).group(1)
        file_password = re.search(r'name="file_password" value="([^"]*)', self.html).group(1)

        challenge = re.search(r"recaptcha/api/challenge\?k=([0-9A-Za-z]+)", self.html)

        options = {"time": time, "time_secure": time_secure, "file_password": file_password}

        if challenge:
            re_captcha = ReCaptcha(self)
            challenge, result = re_captcha.challenge(challenge.group(1))
            options["recaptcha_challenge_field"] = challenge
            options["recaptcha_response_field"] = result

        self.wait()

        pyfile.name = self.get_file_name()

        self.download(self.url, post=options)

        check = self.checkDownload({"wrong_captcha": "Wrong captcha."})
        if check == "wrong_captcha":
            self.process(pyfile)

        
    def download_api_data(self, force=False):
        if self.api_data and not force:
            return
        match = re.compile(self.__pattern__).search(self.pyfile.url)
        if match:
            src = self.load("http://uploaded.to/api/file", cookies=False, get={"id": match.group(1).split("/")[0]}).decode("utf8", "ignore")
            if not src.find("404 Not Found"):
                return
            self.api_data = {}
            lines = src.splitlines()
            self.log.debug("Uploaded API: %s" % lines)
            self.api_data["filename"] = lines[0]
            self.api_data["size"] = int(lines[1]) # in bytes
            self.api_data["checksum"] = lines[2] #sha1

    def download_html(self):
        self.html = self.load(self.pyfile.url, cookies=False).decode("utf8", "ignore")

    def get_waiting_time(self):
        try:
            wait_minutes = re.search(r"Or wait ([\d\-]+) minutes", self.html).group(1)
            if int(wait_minutes) < 0: wait_minutes = 1            
            self.wantReconnect = True
            return 60 * int(wait_minutes)
        except:
            return 0

    def get_file_url(self):
        return self.cleanUrl(self.pyfile.url)

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
        if re.search(r"(File doesn't exist)", self.html) is not None:
            return False
        else:
            return True

    
    def cleanUrl(self, url):
        url = url.replace("ul.to/", "uploaded.to/file/")
        url = url.replace("/?id=", "/file/")
        url = url.replace("?id=", "file/")
        url = re.sub("/\?(.*?)&id=", "/file/", url, 1)
        return url
