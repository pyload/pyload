#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
from module.plugins.Plugin import chunks

from module.network.RequestFactory import getURL
from module.utils import decode

try:
    from json import loads as json_loads
except ImportError: # pragma: no cover
    from module.lib.simplejson import loads as json_loads

def getInfo(urls):
    for chunk in chunks(urls, 20):
        result=[]
        ids=dict()
        for url in chunk:
            id = getId(url)
            if id:
                ids[id]=url
            else:
                result.append((none,0,1,url))

        if len(ids) > 0:
            check_url="http://api.filesonic.com/link?method=getInfo&format=json&ids=" + ",".join(ids.keys())
            response = json_loads(getURL(check_url).decode("utf8","ignore"))
            for item in response["FSApi_Link"]["getInfo"]["response"]["links"]:
                if item["status"] != "AVAILABLE":
                    result.append((None,0,1,ids[item["id"]]))
                else:
                    result.append((item["filename"],item["size"],2,ids[str(item["id"])]))
        yield result

def getId(url):
    match = re.search(FilesonicCom.FILE_ID_PATTERN,url)
    if match:
        return string.replace(match.group("id"),"/","-")
    else:
        return None

class FilesonicCom(Hoster):
    __name__ = "FilesonicCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(sharingmatrix|filesonic)\..*?/file/(([a-z][0-9]+/)?[0-9]+)(/.*)?"
    __version__ = "0.31"
    __description__ = """FilesonicCom und Sharingmatrix Download Hoster"""
    __author_name__ = ("jeix","paulking")
    __author_mail__ = ("jeix@hasnomail.de","")

    URL_DOMAIN_PATTERN = r'(?P<prefix>.*?)(?P<domain>.(filesonic|sharingmatrix)\..+?)(?P<suffix>/.*)'
    FILE_ID_PATTERN = r'/file/(?P<id>([a-z][0-9]+/)?[0-9]+)(/.*)?'
    FILE_LINK_PATTERN = r'<p><a href="(http://.+?\.(filesonic|sharingmatrix)\..+?)"><span>Start download'
    WAIT_TIME_PATTERN = r'countDownDelay = (?P<wait>\d+)'
    WAIT_TM_PATTERN = r"name='tm' value='(.*?)' />"
    WAIT_TM_HASH_PATTERN = r"name='tm_hash' value='(.*?)' />"
    CAPTCHA_TYPE1_PATTERN = r'Recaptcha.create\("(.*?)",'
    CAPTCHA_TYPE2_PATTERN = r'id="recaptcha_image"><img style="display: block;" src="(.+)image?c=(.+?)"'

    def init(self):
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
        if not self.premium:
            self.chunkLimit = 1
            self.multiDL = False

    def process(self, pyfile):

        self.pyfile = pyfile

        self.pyfile.url = self.checkFile(self.pyfile.url)

        if self.premium:
            self.downloadPremium()
        else:
            self.downloadFree()

    def checkFile(self,url):
        id = getId(url)
        self.log.debug("%s: file id is %s" % (self.__name__,id))
        if id:
            # Use the api to check the current status of the file and fixup data
            check_url="http://api.filesonic.com/link?method=getInfo&format=json&ids=%s" % id
            result = json_loads(self.load(check_url).decode("utf8","ignore"))
            item = result["FSApi_Link"]["getInfo"]["response"]["links"][0]
            self.log.debug("%s: api check returns %s" % (self.__name__,item))

            if item["status"] != "AVAILABLE":
                self.offline()
            if item["is_password_protected"] != 0:
                self.fail("This file is password protected")
            if item["is_premium_only"] != 0 and not self.premium:
                self.fail("need premium account for file")
            self.pyfile.name=item["filename"]

            # Fix the url and resolve the domain to the correct regional variation
            url=item["url"]
            urlparts = re.search(self.URL_DOMAIN_PATTERN,url)
            if urlparts:
                url = urlparts.group("prefix")+self.getDomain()+urlparts.group("suffix")
                self.log.debug("%s: localised url is %s" % (self.__name__,url))
            return url
        else:
            self.fail("Invalid URL")

    def getDomain(self):
        result = json_loads(self.load("http://api.filesonic.com/utility?method=getFilesonicDomainForCurrentIp&format=json").decode("utf8","ignore"))
        self.log.debug("%s: response to get domain %s" % (self.__name__,result))
        return result["FSApi_Utility"]["getFilesonicDomainForCurrentIp"]["response"]


    def downloadPremium(self):
        self.log.debug("%s: Premium download" % self.__name__)
        self.download(self.pyfile.url)

    def downloadFree(self):
        self.log.debug("%s: Free download" % self.__name__)
        # Get initial page
        self.html = self.load(self.pyfile.url)
        url = self.pyfile.url + "?start=1"
        self.html = self.load(url)
        self.handleErrors()

        finalUrl = re.search(self.FILE_LINK_PATTERN, self.html)

        if not finalUrl:
            self.doWait(url)
            self.doWait(url)
  
            chall = re.search(self.CAPTCHA_TYPE1_PATTERN, self.html)
            chall2 = re.search(self.CAPTCHA_TYPE2_PATTERN, self.html)
            if chall or chall2:
                for i in range(5):

                    re_captcha = ReCaptcha(self)
                    if chall:
                        self.log.debug("%s: Captcha type1" % self.__name__)
                        challenge, result = re_captcha.challenge(chall.group(1))
                    else:
                        self.log.debug("%s: Captcha type2" % self.__name__)
                        server = chall2.group(1)
                        challenge = chall2.group(2)
                        result = re_captcha.result(server, challenge)

                    postData = {"recaptcha_challenge_field": challenge,
                                "recaptcha_response_field" : result}

                    self.html = self.load(url, post=postData)
                    self.handleErrors()
                    chall = re.search(self.CAPTCHA_TYPE1_PATTERN, self.html)
                    chall2 = re.search(self.CAPTCHA_TYPE2_PATTERN, self.html)

                    if chall or chall2:
                        self.invalidCaptcha()
                    else: 
                        self.correctCaptcha()
                        break

            finalUrl = re.search(self.FILE_LINK_PATTERN, self.html)

        if not finalUrl:
            self.fail("Couldn't find free download link")

        self.log.debug("%s: got download url %s" % (self.__name__, finalUrl.group(1)))
        self.download(finalUrl.group(1))

    def doWait(self, url):
        # If the current page requires us to wait then wait and move to the next page as required
        waitSearch = re.search(self.WAIT_TIME_PATTERN, self.html)
        if waitSearch:
            wait = int(waitSearch.group("wait"))
            if wait > 300:
                self.wantReconnect = True

            self.setWait(wait)
            self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait))
            self.wait()

            tm = re.search(self.WAIT_TM_PATTERN, self.html)
            tm_hash = re.search(self.WAIT_TM_HASH_PATTERN, self.html)

            if tm and tm_hash:
                tm = tm.group(1)
                tm_hash = tm_hash.group(1)
                self.html = self.load(url, post={"tm":tm,"tm_hash":tm_hash})
                self.handleErrors()
            else:
                self.html = self.load(url)
                self.handleErrors()

    def handleErrors(self):
        if "This file is available for premium users only." in self.html:
            self.fail("need premium account for file")

        if "The file that you're trying to download is larger than" in self.html:
            self.fail("need premium account for file")

        if "Free users may only download 1 file at a time" in self.html:
            self.fail("only 1 file at a time for free users")

        if "Free user can not download files" in self.html:
            self.fail("need premium account for file")

        if "Download session in progress" in self.html:
            self.fail("already downloading")

        if "This file is password protected" in self.html:
            self.fail("This file is password protected")

        if "An Error Occurred" in self.html:
            self.fail("A server error occured.")

        if "This file was deleted" in self.html:
            self.offline()
