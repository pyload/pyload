#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo, replace_patterns


def getInfo(urls):
    h = getRequest()
    h.c.setopt(HTTPHEADER,
               ["Accept: text/html",
                "User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"])
    for url in urls:
        html = h.load(url, decode=True)
        file_info = parseFileInfo(ShareRapidCom, replace_patterns(url, ShareRapidCom.FILE_URL_REPLACEMENTS), html)
        yield file_info


class ShareRapidCom(SimpleHoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?((share(-?rapid\.(biz|com|cz|info|eu|net|org|pl|sk)|-(central|credit|free|net)\.cz|-ms\.net)|(s-?rapid|rapids)\.(cz|sk))|(e-stahuj|mediatack|premium-rapidshare|rapidshare-premium|qiuck)\.cz|kadzet\.com|stahuj-zdarma\.eu|strelci\.net|universal-share\.com)/stahuj/(?P<id>\w+)"
    __version__ = "0.53"
    __description__ = """Share-rapid.com plugin - premium only"""
    __author_name__ = ("MikyWoW", "zoidberg", "stickell")
    __author_mail__ = ("MikyWoW@seznam.cz", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'<h1[^>]*><span[^>]*>(?:<a[^>]*>)?(?P<N>[^<]+)'
    FILE_SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong></td>'
    FILE_OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    DOWNLOAD_URL_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'
    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://share-rapid.com/stahuj/\g<id>')]

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.fail("User not logged in")

        try:
            self.html = self.load(pyfile.url, decode=True)
        except BadHeader, e:
            self.account.relogin(self.user)
            self.retry(3, 0, str(e))

        self.getFileInfo()

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if found:
            link = found.group(1)
            self.logDebug("Premium link: %s" % link)

            self.download(link, disposition=True)
        else:
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin(self.user)
                self.retry(3, 0, "User login failed")
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail("Not enough credit left")
            else:
                self.fail("Download link not found")           
