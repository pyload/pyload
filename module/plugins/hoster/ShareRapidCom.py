#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pycurl import HTTPHEADER
from module.network.RequestFactory import getRequest
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo

def getInfo(urls):
    file_info = []
    for url in urls:
        h = getRequest()
        try:
            h.c.setopt(HTTPHEADER, ["Accept: text/html"])
            html = h.load(url, cookies = True, decode = True)
            file_info = parseFileInfo(ShareRapidCom, url, html) 
        finally:
            h.close()
            yield file_info

class ShareRapidCom(SimpleHoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?((share(-?rapid\.(biz|com|cz|info|eu|net|org|pl|sk)|-(central|credit|free|net)\.cz|-ms\.net)|(s-?rapid|rapids)\.(cz|sk))|(e-stahuj|mediatack|premium-rapidshare|rapidshare-premium|qiuck)\.cz|kadzet\.com|stahuj-zdarma\.eu|strelci\.net|universal-share\.com)/(stahuj/.+)"
    __version__ = "0.47"
    __description__ = """Share-rapid.com plugin - premium only"""
    __author_name__ = ("MikyWoW", "zoidberg")
    __author_mail__ = ("MikyWoW@seznam.cz", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<h1[^>]*><span[^>]*>(?:<a[^>]*>)?(?P<N>[^<]+)'
    FILE_SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong></td>'
    DOWNLOAD_URL_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'
    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'
    FILE_OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account: self.fail("User not logged in")
        url = "http://share-rapid.com/" + re.search(self.__pattern__, pyfile.url).groups()[-1]
        self.logDebug("URL: " + url)

        try:
            self.html = self.load(url, decode=True)
        except BadHeader, e:
            self.account.relogin(self.user)
            self.retry(3, 0, str(e))
            
        self.getFileInfo()

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if found is not None:
            link, pyfile.name = found.groups()
            self.logDebug("Premium link: %s" % link)
            self.download(link)
        else:
            self.logError("Download URL not found")
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin()
                self.retry(3,0,"User login failed")
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail("Not enough credit left")
            else:
                self.fail("Download link not found")