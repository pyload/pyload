#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
from module.plugins.Plugin import chunks

from module.network.RequestFactory import getURL

def getInfo(urls):
    for chunk in chunks(urls, 15):
        page = getURL("http://www.filesonic.com/link-checker", post={"links": "\n".join(chunk)}).decode("utf8", "ignore")

        found = re.findall(r'<tr>\s+<td class="source"><span>([^<]+)</span></td>\s+<td class="fileName"><span>([^<]+)</span></td>\s+<td class="fileSize"><span>([0-9]+) MB</span></td>\s+<td class="availability"><span>\s+<strong style="font-weight: strong; color: green;">([^<]+)</strong><br />\s+</span>\s+</td>\s+</tr>', page, re.MULTILINE)
        result = []
        for src, name, size, status in found:
            result.append((name, int(size)*1024*1024, 2 if status == "Available" else 1, src))


        yield result

class FilesonicCom(Hoster):
    __name__ = "FilesonicCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(sharingmatrix|filesonic)\.(com|net)/.*?file/([0-9]+(/.+)?|[a-z0-9]+/[0-9]+(/.+)?)"
    __version__ = "0.2"
    __description__ = """FilesonicCom und Sharingmatrix Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")

    def setup(self):
        self.multiDL = True if self.account else False

    def process(self, pyfile):
        self.pyfile = pyfile
        
        self.url = self.convertURL(self.pyfile.url)
        
        self.html = self.load(self.url, cookies=False)
        name = re.search(r'<title>Download (.*?) for free on Filesonic.com</title>', self.html)
        if name:
            self.pyfile.name = name.group(1)
        else:
            self.offline()
            
        if 'The page you are trying to access was not found.' in self.html:
            self.offline()

        if self.account:
            self.download(pyfile.url)
        else:
            self.download(self.getFileUrl())

    def getFileUrl(self):

        link = self.url + "/" + re.search(r'href="(.*?start=1.*?)"', self.html).group(1)
        self.html = self.load(link)

        self.handleErrors()

        realLinkRegexp = "<p><a href=\"(http://[^<]*?\\.filesonic\\.com[^<]*?)\"><span>Start download now!</span></a></p>"
        url = re.search(realLinkRegexp, self.html)
        
        if not url:
            if "This file is available for premium users only." in self.html:
                self.fail("Need premium account.")
            
            countDownDelay = re.search("countDownDelay = (\\d+)", self.html)
            if countDownDelay:
                wait_time = int(countDownDelay.group(1))
                 
                if wait_time > 300:
                    self.wantReconnect = True
                
                self.setWait(wait_time)
                self.log.info("%s: Waiting %d seconds." % (self.__name__, wait_time))
                self.wait()
                
                tm = re.search("name='tm' value='(.*?)' />", self.html).group(1)
                tm_hash = re.search("name='tm_hash' value='(.*?)' />", self.html).group(1)
                
                self.html = self.load(self.url + "?start=1", post={"tm":tm,"tm_hash":tm_hash})

                self.handleErrors()
            
            
            if "Please Enter Password" in self.html:
                self.fail("implement need pw")
            
            chall = re.search(r'Recaptcha.create\("(.*?)",', self.html)
            for i in range(5):
                if not chall: break

                re_captcha = ReCaptcha(self)
                challenge, result = re_captcha.challenge(chall.group(1))
            
                postData = {"recaptcha_challenge_field": challenge,
                            "recaptcha_response_field" : result}
                            
                self.html = self.load(link, post=postData)
                chall = re.search(r'Recaptcha.create\("(.*?)",', self.html)

                if chall:
                    self.invalidCaptcha()

        url = re.search(realLinkRegexp, self.html).group(1)
        return url
        
    def convertURL(self, url):
        id = re.search("/file/([0-9]+(/.+)?)", url)
        if not id:
            id = re.search("/file/[a-z0-9]+/([0-9]+(/.+)?)", url)
        return "http://www.filesonic.com/file/" + id.group(1)

    def handleErrors(self):
        if "The file that you're trying to download is larger than" in self.html:
            self.fail("need premium account for file")

        if "Free users may only download 1 file at a time" in self.html:
            self.fail("only 1 file at a time for free users")

        if "Free user can not download files" in self.html:
            self.fail("need premium account for file")
            
        if "Download session in progress" in self.html:
            self.fail("already downloading")
                
        if "This file is password protected" in self.html:
            self.fail("This file is password protected, please one.")
            
        if "An Error Occurred" in self.html:
            self.fail("A server error occured.")

