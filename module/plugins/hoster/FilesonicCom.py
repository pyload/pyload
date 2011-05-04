#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
from module.plugins.Plugin import chunks

from module.network.RequestFactory import getURL
from module.utils import decode


def getInfo(urls):
    for chunk in chunks(urls, 15):
        # Always use "filesonic.com" for file's url
        # mod_link contains the right url to check
        orig_link = "".join(chunk)
        mod_link = orig_link
        url_datas = re.search("(.+)(filesonic\..+)/file/(.+)", orig_link)
        if url_datas:
            mod_link = url_datas.group(1) + "filesonic.com" + "/file/" + url_datas.group(3)
        
        page = getURL("http://www." + getDomain() + "/link-checker", post={"links": mod_link}).decode("utf8", "ignore")
        
        found = re.findall(r'<tr>\s+<td class="source"><span>([^<]+)</span></td>\s+<td class="fileName"><span>([^<]+)</span></td>\s+<td class="fileSize"><span>(.+) MB</span></td>\s+<td class="availability"><span>\s+<strong style="font-weight: strong; color: green;">([^<]+)</strong><br />\s+</span>\s+</td>\s+</tr>', page, re.MULTILINE)
        result = []
        for src, name, size, status in found:
            result.append((name, float(size)*1024*1024, 2 if status == "Available" else 1, src))
        yield result
    
def getDomain():
    html = decode(getURL("http://api.filesonic.com/utility?method=getFilesonicDomainForCurrentIp&format=xml"))
    return re.search(r"response>.*?(filesonic\..*?)</resp", html).group(1)
    
class FilesonicCom(Hoster):
    __name__ = "FilesonicCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(sharingmatrix|filesonic)\..*?/.*?file/([0-9]+(/.+)?|[a-z0-9]+/[0-9]+(/.+)?)"
    __version__ = "0.22"
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
        part_1_link = re.search("(.+/file/\d+/)", self.url).group(1)
        link = part_1_link + re.search(r'href="(.*?start=1.*?)"', self.html).group(1)
        self.html = self.load(link)

        self.handleErrors()

        realLinkRegexp = "<p><a href=\"(http://[^<]*?\\.filesonic\\.(com|it)[^<]*?)\"><span>Start download now!</span></a></p>"
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
                
                tm = re.search("name='tm' value='(.*?)' />", self.html)
                tm_hash = re.search("name='tm_hash' value='(.*?)' />", self.html)

                if tm and tm_hash:
                    tm = tm.group(1)
                    tm_hash = tm_hash.group(1)
                else:
                    self.html = self.load(link)
                    self.handleErrors()
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
                else: 
                    self.correctCaptcha()
                    
            re_url = re.search(realLinkRegexp, self.html)
            if re_url:
                url = re_url.group(1)
                    
        if not url:
            self.fail("Plugin failed")
            
        return url
        
    def convertURL(self, url):
        id = re.search("/file/([0-9]+(/.+)?)", url)
        if not id:
            id = re.search("/file/[a-z0-9]+/([0-9]+(/.+)?)", url)
        result = "http://www.filesonic.com/file/" + id.group(1)
        return self.getRightUrl(result)

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

        if "This file was deleted" in self.html:
            self.offline()

    def getRightUrl(self, url):
        part_2 = re.search("http://www..+(/file.+)", url)
        if not part_2:
            part_2 = re.search("http://.+(/file.+)", url)
        return "http://www.%s%s" % (getDomain(), part_2.group(1))
