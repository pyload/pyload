# -*- coding: utf-8 -*-

import re

from pycurl import error

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.ReCaptcha import ReCaptcha
from module.utils import parseFileSize

def parseInfos(html):
        match = re.search(r'id="filename">([^<]+)</a><br /><small>([^<]+)', html)
        return {"name" : match.group(1),
                "size": parseFileSize(match.group(2))}

def getInfo(urls):
    pattern = re.compile(UploadedTo.__pattern__)
    for chunk in chunks(urls, 10):
        result = []
        for url in chunk:
            match = pattern.search(url)
            if match:
                src = getURL(url, get={"id": match.group(1).split("/")[0]}).decode("utf8", "ignore")
                if '<small class="cL">Error: 404</small></h1>' in src:
                    result.append((url, 0, 1, url))
                    continue
                    
                data = parseInfos(src)
                result.append((data["name"], data["size"], 2, url))
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
        self.data = {}
        self.multiDL = False
        self.url = False
        if self.account:
            self.multiDL = True
            self.chunkLimit = -1
            self.resumeDownload = True


        self.pyfile.url = self.cleanUrl(self.pyfile.url)
        self.fileID = re.search(self.__pattern__, self.pyfile.url).group(1)

    def process(self, pyfile):
        self.req.cj.setCookie("uploaded.to", "lang", "en")

        self.html = self.load(self.pyfile.url, cookies=False, utf8=True)

        if re.search(r'File doesn\'t exist|<small class="cL">Error: 404</small></h1>', self.html) is not None:
            self.offline()

        self.data = parseInfos(self.html)
        pyfile.name = self.data["name"]

        # self.pyfile.name = self.get_file_name()
        self.premium = self.account.getAccountInfo(self.user)

        if self.account and self.premium:
            self.handlePremium()
        else:
            self.handleFree()


    def handlePremium(self):
        info = self.account.getAccountInfo(self.user, True)
        self.log.debug("%(name)s: Use Premium Account (%(left)sGB left)" % {"name" :self.__name__, "left" : info["trafficleft"]/1024/1024})
        if self.data["size"]/1024 > info["trafficleft"]:
            self.log.info(_("%s: Not enough traffic left" % self.__name__))
            self.account.empty()
            self.resetAccount()
            self.fail(_("Traffic exceeded"))

        try:
            html = self.load(self.pyfile.url, utf8=True)
        except error, e:
            if e.args and e.args[0] == 23:
                self.log.warning(_("Deactivate direct downloads in your Uploaded.to Account settings."))
                self.download(self.pyfile.url)
        else:
            url = re.search(r'action="(http://.*\.uploaded.to/dl\?id=[^"]+)', html)
            url = url.group(1)
            self.download(url)


    def handleFree(self):

        wait = re.search(r"Current waiting period: <span>(\d+)</span> seconds", self.html).group(1)
        self.setWait(wait)

        js = self.load("http://uploaded.to/js/download.js")

        challengeId = re.search(r'Recaptcha\.create\("([^"]+)', js)

        url = "http://uploaded.to/io/ticket/captcha/%s" % self.fileID
        downloadURL = ""

        for i in range(5):
            self.req.lastURL = str(self.url)
            re_captcha = ReCaptcha(self)
            challenge, result = re_captcha.challenge(challengeId.group(1))
            options = {"recaptcha_challenge_field" : challenge, "recaptcha_response_field": result}
            self.wait()

            result = self.load(url, post=options)
            self.log.debug("UploadedTo result: %s" % result)

            if "limit-dl" in result:
                self.setWait(30 * 60, True)
                self.wait()
                self.retry()
            elif 'err:"captcha"' in result:
                self.invalidCaptcha()
            elif "type:'download'" in result:
                downloadURL = re.search("url:'([^']+)", result).group(1)
                break
                
        if not downloadURL:
            self.fail("No Download url retrieved")

        self.download(downloadURL)

    def cleanUrl(self, url):
        url = url.replace("ul.to/", "uploaded.to/file/")
        url = url.replace("/?id=", "/file/")
        url = url.replace("?id=", "file/")
        url = re.sub("/\?(.*?)&id=", "/file/", url, 1)
        return url
