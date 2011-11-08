#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(re.sub(r"\.com(/.*?)?/files", ".com/en/files", url), decode=True)
        if re.search(DepositfilesCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(DepositfilesCom.FILE_INFO_PATTERN, html)
            if found is not None:
                name, size, units = found.groups()
                size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]
                result.append((name, size, 2, url))
    yield result

class DepositfilesCom(Hoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?depositfiles\.com(/\w{1,3})?/files/[\w]+"
    __version__ = "0.34"
    __description__ = """Depositfiles.com Download Hoster"""
    __author_name__ = ("spoob", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'File name: <b title="([^"]+)">.*\s*<span class="nowrap">File size: <b>([0-9.]+)&nbsp;(KB|MB|GB)</b>'
    FILE_OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'
    RECAPTCHA_PATTERN = r"Recaptcha.create\('([^']+)', this\);"
    DOWNLOAD_LINK_PATTERN = r'<form action="(http://.+?\.depositfiles.com/.+?)" method="get"'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False

        self.pyfile.url = re.sub(r"\.com(/.*?)?/files", ".com/en/files", self.pyfile.url)

    def process(self, pyfile):

        if re.search(r"(.*)\.html", self.pyfile.url):
            self.pyfile.url = re.search(r"(.*)\.html", self.pyfile.url).group(1)

        self.html = self.load(self.pyfile.url, cookies=True if self.account else False, decode = True)

        if self.FILE_OFFLINE_PATTERN in self.html:
            self.offline()

        pyfile.name, size, units = re.search(self.FILE_INFO_PATTERN, self.html).groups()
        pyfile.size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]
        self.logDebug ("FILENAME: %s" % pyfile.name)
        #return_url = self.req.lastEffectiveURL.split("/", 3)[3]
        #self.html = self.load(r'http://depositfiles.com/switch_lang.php?return_url=%s&lang=en' % return_url)

        #pyfile.name = re.search('(?s)Dateiname: <b title=\"(.*?)\">.*?</b>', self.html).group(1)

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

        found = re.search(r"var fid = '(\w+)';", self.html)
        if not found: self.retry(wait_time=5)
        params = {'fid' : found.group(1)}
        self.logDebug ("FID: %s" % params['fid'])

        captcha_key = None
        found = re.search(self.RECAPTCHA_PATTERN, self.html)
        if found: captcha_key = found.group(1)
        self.logDebug ("CAPTCHA_KEY: %s" % captcha_key)

        self.wait()
        recaptcha = ReCaptcha(self)

        for i in range(5):
            self.html = self.load("http://depositfiles.com/get_file.php", get = params)
            if '<input type=button value="Continue" onclick="check_recaptcha' in self.html:
                if not captcha_key: self.fail('Parse error (Captcha key)')
                if 'response' in params: self.invalidCaptcha()
                params['challenge'], params['response'] = recaptcha.challenge(captcha_key)
                self.logDebug(params)
                continue

            found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
            if found:
                if 'response' in params: self.correctCaptcha()
                link = urllib.unquote(found.group(1))
                self.logDebug ("LINK: %s" % link)
                break
            else:
                self.fail('Parse error (Download link)')
        else:
            self.fail('No valid captcha response received')

        try:
            self.download(link)
        except:
            self.retry(wait_time = 60)

    def handlePremium(self):
        link = urllib.unquote(re.search('<div id="download_url">\s*<a href="(http://.+?\.depositfiles.com/.+?)"', self.html).group(1))
        self.download(link)