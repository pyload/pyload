from random import randint
from helper import *
from os.path import join
from logging import getLogger
import zlib

from CookieJar import CookieJar
from HTTPBase import HTTPBase
from HTTPDownload import HTTPDownload
from FTPBase import FTPDownload
from XDCCBase import XDCCDownload

from traceback import print_stack

class Browser(object):
    def __init__(self, interface=None, cookieJar=None, bucket=None, proxies={}):
        self.log = getLogger("log")

        self.lastURL = None
        self.interface = interface
        self.bucket = bucket

        self.http = HTTPBase(interface=interface, proxies=proxies)
        self.setCookieJar(cookieJar)
        self.proxies = proxies
        self.abort = property(lambda: False, lambda val: self.abortDownloads() if val else None)
        
        self.downloadConnections = []

    def setCookieJar(self, cookieJar):
        self.cookieJar = cookieJar
        self.http.cookieJar = self.cookieJar

    def clearCookies(self):
        self.cookieJar.clear()

    def clearReferer(self):
        self.lastURL = None

    def getPage(self, url, get={}, post={}, referer=None, cookies=True, customHeaders={}):
        if not referer:
            referer = self.lastURL
        self.http.followRedirect = True
        resp = self.http.getResponse(url, get=get, post=post, referer=referer, cookies=cookies,
                                     customHeaders=customHeaders)
        data = resp.read()
        try:
            if resp.info()["Content-Encoding"] == "gzip":
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)
            elif resp.info()["Content-Encoding"] == "deflate":
                data = zlib.decompress(data, -zlib.MAX_WBITS)
        except:
            pass

        try:
            content_type = resp.info()["Content-Type"]
            infos = [info.strip() for info in content_type.split(";")]
            charset = None
            for info in infos:
                if info.startswith("charset"):
                    none, charset = info.split("=")
            if charset:
                data = data.decode(charset)
        except Exception, e:
            self.log.debug("Could not decode charset: %s" % e)

        self.lastURL = resp.geturl()
        return data

    def getRedirectLocation(self, url, get={}, post={}, referer=None, cookies=True, customHeaders={}):
        if not referer:
            referer = self.lastURL
        self.http.followRedirect = False
        resp = self.http.getResponse(url, get=get, post=post, referer=referer, cookies=cookies,
                                     customHeaders=customHeaders)
        resp.close()
        self.lastURL = resp.geturl()
        location = None
        try:
            location = resp.info()["Location"]
        except:
            pass
        return location
    
    def _removeConnection(self, *args, **kwargs):
        i = self.downloadConnections.index(args[-1])
        self.downloadConnections[i].download.clean()
        del self.downloadConnections[i]
    
    def abortDownloads(self):
        for d in self.downloadConnections:
            d.download.setAbort(True)
            d.abort = True

    @property
    def speed(self):
        speed = 0
        for d in self.downloadConnections:
            speed += d.speed
        return speed
    
    def httpDownload(self, url, filename, get={}, post={}, referer=None, cookies=True, customHeaders={}, chunks=1,
                     resume=False):
        if not referer:
            referer = self.lastURL

        dwnld = HTTPDownload(url, filename, get=get, post=post, referer=referer, cookies=cookies,
                             customHeaders=customHeaders, bucket=self.bucket, interface=self.interface,
                             proxies=self.proxies)
        dwnld.cookieJar = self.cookieJar

        d = dwnld.download(chunks=chunks, resume=resume)
        self.downloadConnections.append(d)
        d.addCallback(self._removeConnection, d)
        d.addErrback(self._removeConnection, d)
        return d

    def ftpDownload(self, url, filename, resume=False):
        dwnld = FTPDownload(url, filename, bucket=self.bucket, interface=self.interface, proxies=self.proxies)

        d = dwnld.download(resume=resume)
        self.downloadConnections.append(d)
        d.addCallback(self._removeConnection, d)
        return d

    def xdccDownload(self, server, port, channel, bot, pack, filename, nick="pyload_%d" % randint(1000, 9999),
                     ident="pyload", real="pyloadreal"):
        dwnld = XDCCDownload(server, port, channel, bot, pack, nick, ident, real, filename, bucket=self.bucket,
                             interface=self.interface, proxies=self.proxies)

        d = dwnld.download()
        self.downloadConnections.append(d)
        d.addCallback(self._removeConnection, d)
        return d
    
    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, no_post_encode=False, raw_cookies={}):
        self.log.warning("Browser: deprecated call 'load'")
        print_stack()
        return self.getPage(url, get=get, post=post, cookies=cookies)

    def download(self, url, file_name, folder, get={}, post={}, ref=True, cookies=True, no_post_encode=False):
        #@TODO
        self.log.warning("Browser: deprecated call 'download'")
        print_stack()

        filename = join(folder, file_name)
        d = self.httpDownload(url, filename, get, post)
        waitFor(d)

        return filename

    def clean(self):
        """ cleanup """
        if hasattr(self, "http"):
            self.http.clean()
            del self.http

if __name__ == "__main__":
    browser = Browser()#proxies={"socks5": "localhost:5000"})
    ip = "http://www.whatismyip.com/automation/n09230945.asp"
    #browser.getPage("http://google.com/search?q=bar")
    #browser.getPage("https://encrypted.google.com/")
    #print browser.getPage(ip)
    #print browser.getRedirectLocation("http://google.com/")
    #browser.getPage("https://encrypted.google.com/")
    #browser.getPage("http://google.com/search?q=bar")

    browser.httpDownload("http://speedtest.netcologne.de/test_100mb.bin", "test_100mb.bin")
    from time import sleep

    while True:
        sleep(1)
