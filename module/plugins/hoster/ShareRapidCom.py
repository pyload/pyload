#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pycurl import HTTPHEADER
from module.network.RequestFactory import getRequest, getURL
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.common.json_layer import json_loads

def checkFile(url):    
    info = {"name" : url, "size" : 0, "status" : 3}
    
    response = getURL("http://share-rapid.com/checkfiles.php", post = {"files": url}, decode = True)
    info = json_loads(response)

    if "error" in info:
        if info['error'] == False:
            info['name'] = info['filename']
            info['status'] = 2
        elif info['msg'] == "Not found":
            info['status'] = 1 #offline
        elif info['msg'] == "Service Unavailable":
            info['status'] = 6 #temp.offline

    return info
    
def getInfo(urls):
    for url in urls:
        info = checkFile(url)
        if "filename" in info:
            yield info['name'], info['size'], info['status'], url
        else:        
            file_info = (url, 0, 3, url)
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
    __pattern__ = r"http://(?:www\.)?((share(-?rapid\.(biz|com|cz|info|eu|net|org|pl|sk)|-(central|credit|free|net)\.cz|-ms\.net)|(s-?rapid|rapids)\.(cz|sk))|(e-stahuj|mediatack|premium-rapidshare|rapidshare-premium|qiuck)\.cz|kadzet\.com|stahuj-zdarma\.eu|strelci\.net|universal-share\.com)/stahuj/(.+)"
    __version__ = "0.50"
    __description__ = """Share-rapid.com plugin - premium only"""
    __author_name__ = ("MikyWoW", "zoidberg")
    __author_mail__ = ("MikyWoW@seznam.cz", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<h1[^>]*><span[^>]*>(?:<a[^>]*>)?(?P<N>[^<]+)'
    FILE_SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong></td>'
    FILE_OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'
    
    DOWNLOAD_URL_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'
    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account: self.fail("User not logged in")  
                       
        self.info = checkFile(pyfile.url)
        self.logDebug(self.info)
        
        pyfile.status = self.info['status']          
        
        if pyfile.status == 2:
            pyfile.name = self.info['name']
            pyfile.size = self.info['size']
        elif pyfile.status == 1: 
            self.offline()
        elif pyfile.status == 6:
            self.tempOffline()
        else:
            self.fail("Unexpected file status")
        
        url = "http://share-rapid.com/stahuj/%s" % self.info['filepath']
        try:
            self.html = self.load(url, decode=True)
        except BadHeader, e:
            self.account.relogin(self.user)
            self.retry(3, 0, str(e))

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if found is not None:
            link = found.group(1)            
            self.logDebug("Premium link: %s" % link)
            
            self.check_data = {"size": pyfile.size}
            self.download(link)
        else:
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin(self.user)
                self.retry(3,0,"User login failed")
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail("Not enough credit left")
            else:
                self.fail("Download link not found")           