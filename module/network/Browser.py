from HTTPBase import HTTPBase
from HTTPDownload import HTTPDownload

from os.path import exists

import zlib
from cookielib import CookieJar
from FTPBase import FTPDownload

class Browser():
    def __init__(self, interface=None, cookieJar=CookieJar(), bucket=None, proxies={}):
        self.lastURL = None
        self.interface = interface
        self.cookieJar = cookieJar
        self.bucket = bucket
        
        self.http = HTTPBase(interface=interface, proxies=proxies)
        self.http.cookieJar = cookieJar
        self.proxies = proxies
    
    def clearReferer(self):
        self.lastURL = None
    
    def getPage(self, url, get={}, post={}, referer=None, cookies=True, customHeaders={}):
        if not referer:
            referer = self.lastURL
        self.http.followRedirect = True
        resp = self.http.getResponse(url, get=get, post=post, referer=referer, cookies=cookies, customHeaders=customHeaders)
        data = resp.read()
        try:
            if resp.info()["Content-Encoding"] == "gzip":
                data = zlib.decompress(data, 16+zlib.MAX_WBITS)
            elif resp.info()["Content-Encoding"] == "deflate":
                data = zlib.decompress(data, -zlib.MAX_WBITS)
        except:
            pass
        self.lastURL = resp.geturl()
        return data
    
    def getRedirectLocation(self, url, get={}, post={}, referer=None, cookies=True, customHeaders={}):
        if not referer:
            referer = self.lastURL
        self.http.followRedirect = False
        resp = self.http.getResponse(url, get=get, post=post, referer=referer, cookies=cookies, customHeaders=customHeaders)
        resp.close()
        self.lastURL = resp.geturl()
        location = None
        try:
            location = resp.info()["Location"]
        except:
            pass
        return location
    
    def httpDownload(self, url, filename, get={}, post={}, referer=None, cookies=True, customHeaders={}, chunks=1, resume=False):
        if not referer:
            referer = self.lastURL
        
        dwnld = HTTPDownload(url, filename, get=get, post=post, referer=referer, cookies=cookies, customHeaders=customHeaders, bucket=self.bucket, interface=self.interface, proxies=self.proxies)
        dwnld.cookieJar = self.cookieJar
        
        d = dwnld.download(chunks=chunks, resume=resume)
        return d
    
    def ftpDownload(self, url, filename, resume=False):
        dwnld = FTPDownload(url, filename, bucket=self.bucket, interface=self.interface, proxies=self.proxies)
        
        d = dwnld.download(resume=resume)
        return d

if __name__ == "__main__":
    browser = Browser(proxies={"socks5": "localhost:5000"})
    ip = "http://www.whatismyip.com/automation/n09230945.asp"
    #browser.getPage("http://google.com/search?q=bar")
    #browser.getPage("https://encrypted.google.com/")
    print browser.getPage(ip)
    #print browser.getRedirectLocation("http://google.com/")
    #browser.getPage("https://encrypted.google.com/")
    #browser.getPage("http://google.com/search?q=bar")
    
    #browser.downloadFile("http://speedtest.netcologne.de/test_100mb.bin", "test_100mb.bin")
