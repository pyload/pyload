#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import unquote
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha

class DepositfilesCom(SimpleHoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?depositfiles\.com(/\w{1,3})?/files/[\w]+"
    __version__ = "0.42"
    __description__ = """Depositfiles.com Download Hoster"""
    __author_name__ = ("spoob", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'File name: <b title="(?P<N>[^"]+)'
    FILE_SIZE_PATTERN = r'File size: <b>(?P<S>[0-9.]+)&nbsp;(?P<U>[kKMG])i?B</b>'
    FILE_INFO_PATTERN = r'<script type="text/javascript">eval\( unescape\(\'(?P<N>.*?)\''
    FILE_OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'
    FILE_URL_REPLACEMENTS = [(r"\.com(/.*?)?/files", ".com/en/files"), (r"\.html$", "")]
    FILE_NAME_REPLACEMENTS = [(r'\%u([0-9A-Fa-f]{4})', lambda m: unichr(int(m.group(1), 16))), (r'.*<b title="(?P<N>[^"]+).*', "\g<N>" )]

    RECAPTCHA_PATTERN = r"Recaptcha.create\('([^']+)'"
    DOWNLOAD_LINK_PATTERN = r'<form action="(http://.+?\.depositfiles.com/.+?)" method="get"'

    def setup(self):
        self.multiDL = False
        self.resumeDownload = self.premium

    def handleFree(self):
        self.html = self.load(self.pyfile.url, post={"gateway_result":"1"}, cookies = True)
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()

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

        captcha_key = '6LdRTL8SAAAAAE9UOdWZ4d0Ky-aeA7XfSqyWDM2m'
        found = re.search(self.RECAPTCHA_PATTERN, self.html)
        if found: captcha_key = found.group(1)
        self.logDebug ("CAPTCHA_KEY: %s" % captcha_key)

        self.wait()
        recaptcha = ReCaptcha(self)

        for i in range(5):
            self.html = self.load("http://depositfiles.com/get_file.php", get = params)

            if '<input type=button value="Continue" onclick="check_recaptcha' in self.html:
                if not captcha_key: self.parseError('Captcha key')
                if 'response' in params: self.invalidCaptcha()
                params['challenge'], params['response'] = recaptcha.challenge(captcha_key)
                self.logDebug(params)
                continue

            found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
            if found:
                if 'response' in params: self.correctCaptcha()
                link = unquote(found.group(1))
                self.logDebug ("LINK: %s" % link)
                break
            else:
                self.parseError('Download link')
        else:
            self.fail('No valid captcha response received')

        try:
            self.download(link, disposition = True)
        except:
            self.retry(wait_time = 60)

    def handlePremium(self):
        if '<span class="html_download_api-gold_traffic_limit">' in self.html:
            self.logWarning("Download limit reached")
            self.retry(25, 3600, "Download limit reached")
        elif 'onClick="show_gold_offer' in self.html:
            self.account.relogin(self.user)
            self.retry()
        link = unquote(re.search('<div id="download_url">\s*<a href="(http://.+?\.depositfiles.com/.+?)"', self.html).group(1))
        self.multiDL = True
        self.download(link, disposition = True)

getInfo = create_getInfo(DepositfilesCom)