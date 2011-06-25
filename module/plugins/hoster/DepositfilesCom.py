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
        self.resumeDownload = self.multiDL = True if self.account else False

        self.pyfile.url = re.sub(r"\.com(/.*?)?/files", ".com/de/files", self.pyfile.url)
        
    def process(self, pyfile):

        if re.search(r"(.*)\.html", self.pyfile.url):
            self.pyfile.url = re.search(r"(.*)\.html", self.pyfile.url).group(1)

        self.html = self.load(self.pyfile.url, cookies=True if self.account else False)
        
        if '<span class="html_download_api-not_exists"></span>' in self.html:
            self.offline()
            
        
        
        return_url = self.req.lastEffectiveURL.split("/", 3)[3]
        self.html = self.load(r'http://depositfiles.com/switch_lang.php?return_url=%s&lang=de' % return_url)

        pyfile.name = re.search('(?s)Dateiname: <b title=\"(.*?)\">.*?</b>', self.html).group(1)

        if self.account:
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):

        self.html = self.load(self.pyfile.url, post={"gateway_result":"1"})

        if re.search(r'File is checked, please try again in a minute.', self.html) is not None:
            self.log.info("DepositFiles.com: The file is being checked. Waiting 1 minute.")
            self.setWait(61)
            self.wait()
            self.retry()
            
        wait = re.search(r'html_download_api-limit_interval\">(\d+)</span>', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.log.info( "%s: Traffic used up. Waiting %d seconds." % (self.__name__, wait_time) )
            self.setWait(wait_time)
            self.wantReconnect = True
            self.wait()
            self.retry()

        wait = re.search(r'>Try in (\d+) minutes or use GOLD account', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.log.info( "%s: All free slots occupied. Waiting %d minutes." % (self.__name__, wait_time) )
            self.setWait(wait_time * 60, False)

        wait = re.search(r'Please wait (\d+) sec', self.html)
        if wait:
            self.setWait(int(wait.group(1)))

        self.wait()

        form = re.search(r"\$\('#download_container'\)\.load\('([^']+)", self.html)

        self.html = self.load("http://depositfiles.com/"+ form.group(1))

        link = urllib.unquote(re.search('<form action="(http://.+?\.depositfiles.com/.+?)" method="get"', self.html).group(1))
        self.download(link)

            
        #wait_time = int(re.search(r'<span id="download_waiter_remain">(.*?)</span>', self.html).group(1))
        #self.setWait(wait_time)
        #self.log.debug("DepositFiles.com: Waiting %d seconds." % wait_time)

    def handlePremium(self):
        link = urllib.unquote(re.search('<div id="download_url">\s*<a href="(http://.+?\.depositfiles.com/.+?)"', self.html).group(1))
        self.download(link)
