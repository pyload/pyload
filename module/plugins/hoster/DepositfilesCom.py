#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class DepositfilesCom(Hoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?depositfiles\.com(/\w{1,3})?/files/[\w]+"
    __version__ = "0.32"
    __description__ = """Depositfiles.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def setup(self):
        self.req.canContinue = self.multiDL = True if self.account else False
        
    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, cookies=True if self.account else False)
        
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights", self.html):
            self.offline()
        
        if not self.account:
            self.handleFree()
        
        try:
            pyfile.name = re.search('File name: <b title="(.*)">', self.html).group(1)
        except:
            pyfile.name = re.search('Dateiname: <b title="(.*)">', self.html).group(1)
        
        if self.account:
            link = urllib.unquote(re.search('<div id="download_url">\s*<a href="(http://.+?\.depositfiles.com/.+?)"', self.html).group(1))
        else:
            link = urllib.unquote(re.search('<form action="(http://.+?\.depositfiles.com/.+?)" method="get"', self.html).group(1))
        
        self.download(link)

    def handleFree(self):
        tmp_url = self.pyfile.url
        match = re.search(r"depositfiles.com/(?:(?P<lang>[\w]{1,3})/)?files/(?P<id>[\w]+)", tmp_url)
        if match:
            if match.group("id"):
                tmp_url = "http://depositfiles.com/en/files/" + match.group("id")


        if re.search(r'File is checked, please try again in a minute.', self.html) is not None:
            self.log.info("DepositFiles.com: The file is being checked. Waiting 1 minute.")
            self.setWait(61)
            self.wait()
            self.retry()
            
        if re.search(r'Such file does not exist or it has been removed for infringement of copyrights', self.html) is not None:
            self.offline()
            
        self.html = self.load(tmp_url, post={"gateway_result":"1"})
        
        m = re.search(r'<span class="html_download_api-limit_interval">(\d+)</span>', self.html)
        if m is not None:
            wait_time = int( m.group(1) )
            self.log.info( "%s: Traffic used up. Waiting %d seconds." % (self.__name__, wait_time) )
            self.setWait(wait_time)
            if wait_time > 300:
                self.wantReconnect = True
            self.wait()
            
            self.html = self.load(tmp_url, post={"gateway_result":"1"})

            
        #wait_time = int(re.search(r'<span id="download_waiter_remain">(.*?)</span>', self.html).group(1))
        #self.setWait(wait_time)
        #self.log.debug("DepositFiles.com: Waiting %d seconds." % wait_time)
