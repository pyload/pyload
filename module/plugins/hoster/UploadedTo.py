# -*- coding: utf-8 -*-

import re

from module.utils import decode

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.ReCaptcha import ReCaptcha

key = reduce(lambda x,y: x+chr(y), [(i+2)^ord(x) for i,x in enumerate("jS1\\50}eSm~5i\\cB+$XVB s^/\\mm&JUF")], "")

def correctDownloadLink(url):
    url = re.sub("http://.*?/", "http://uploaded.to/",url, 1)
    url = re.sub("\\.to/.*?id=", ".to/file/", url, 1)

    if "/file/" not in url:
        url = url.replace("uploaded.to/", "uploaded.to/file/")

    parts = url.split("/")
    return "/".join(parts[:min(5,len(parts))]) + "/"

def getID(url):
    """ returns id of corrected url"""
    return re.search(r"uploaded.to/file/([^/]+)", url).group(1)

def getAPIData(urls):
        post = {"apikey" : key}

        idMap = {}

        for i, url in enumerate(urls):
            newUrl = correctDownloadLink(url)
            id = getID(newUrl)
            post["id_%s" % i] = id
            idMap[id] = url

        api = getURL("http://uploaded.to/api/filemultiple", post=post, decode=True)

        result = {}

        for line in api.splitlines():
            data = line.split(",")
            if idMap.has_key(data[1]):
                result[data[1]] = (data[0], data[2], data[4], data[3], idMap[data[1]])

        return result

def getInfo(urls):
    for chunk in chunks(urls, 80):
        result = []

        api = getAPIData(chunk)

        for data in api.itervalues():
            if data[0] == "online":
                result.append((data[2], data[1], 2, data[4]))

            else:
                result.append((data[4], 0, 1, data[4]))

        yield result

class UploadedTo(Hoster):
    __name__ = "UploadedTo"
    __type__ = "hoster"
    __pattern__ = r"(http://[\w\.-]*?uploaded\.to/.*?(file/|\?id=|&id=)[\w]+/?)|(http://[\w\.]*?ul\.to/(\?id=|&id=)?[\w\-]+/.+)|(http://[\w\.]*?ul\.to/(\?id=|&id=)?[\w\-]+/?)"
    __version__ = "0.51"
    __description__ = """Uploaded.to Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    
    def setup(self):
        self.html = None
        self.multiDL = False
        self.resumeDownload = False
        self.url = False
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
            if self.premium:
                self.multiDL = True
                self.chunkLimit = -1
                self.resumeDownload = True


        self.pyfile.url = correctDownloadLink(self.pyfile.url)
        self.fileID = getID(self.pyfile.url)

    def process(self, pyfile):
        self.req.cj.setCookie("uploaded.to", "lang", "en")


        api = getAPIData([pyfile.url])

        if not len(api) or not api.has_key(self.fileID):
            self.offline()

        self.data = api[self.fileID]
        if self.data[0] != "online":
            self.offline()

        pyfile.name = self.data[2]

        # self.pyfile.name = self.get_file_name()

        if self.account and self.premium:
            self.handlePremium()
        else:
            self.handleFree()


    def handlePremium(self):
        info = self.account.getAccountInfo(self.user, True)
        self.log.debug("%(name)s: Use Premium Account (%(left)sGB left)" % {"name" :self.__name__, "left" : info["trafficleft"]/1024/1024})
        if int(self.data[1])/1024 > info["trafficleft"]:
            self.log.info(_("%s: Not enough traffic left" % self.__name__))
            self.account.empty(self.user)
            self.resetAccount()
            self.fail(_("Traffic exceeded"))

        self.download("http://uploaded.to/file/%s/ddl" % self.fileID)


    def handleFree(self):

        self.html = self.load(self.pyfile.url, decode=True)

        wait = re.search(r"Current waiting period: <span>(\d+)</span> seconds", self.html).group(1)
        self.setWait(wait)

        js = self.load("http://uploaded.to/js/download.js", decode=True)

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
            self.logDebug("result: %s" % result)

            if "limit-size" in result:
                self.fail("File too big for free download")
            elif "limit-slot" in result: # Temporary restriction so just wait a bit
                self.setWait(30 * 60, True)
                self.wait()
                self.retry()
            elif "limit-parallel" in result:
                self.fail("Cannot download in parallel")			 
            elif "limit-dl" in result:
                self.setWait(30 * 60, True)
                self.wait()
                self.retry()
            elif 'err:"captcha"' in result:
                self.invalidCaptcha()
            elif "type:'download'" in result:
                self.correctCaptcha()
                downloadURL = re.search("url:'([^']+)", result).group(1)
                break
                
        if not downloadURL:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.download(downloadURL)
