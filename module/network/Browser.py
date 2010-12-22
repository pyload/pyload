from random import randint
from helper import *
from os.path import join
from logging import getLogger
from cookielib import CookieJar
import zlib

from HTTPBase import HTTPBase
from HTTPDownload import HTTPDownload
from FTPBase import FTPDownload
from XDCCBase import XDCCDownload

class Browser(object):
    def __init__(self, interface=None, cookieJar=CookieJar(), bucket=None, proxies={}):
        self.log = getLogger("log")

        self.lastURL = None
        self.interface = interface
        self.cookieJar = cookieJar
        self.bucket = bucket

        self.http = HTTPBase(interface=interface, proxies=proxies)
        self.setCookieJar(cookieJar)
        self.proxies = proxies

    def setCookieJar(self, cookieJar):
        self.http.cookieJar = cookieJar

    def clearCookies(self):
        pass #@TODO

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

    def download(self, url, file_name, folder, get={}, post={}, ref=True, cookies=True, no_post_encode=False):
        #@TODO

        filename = join(folder, file_name)
        d = self.httpDownload(url, filename, get, post)
        waitFor(d)

        return filename

    def httpDownload(self, url, filename, get={}, post={}, referer=None, cookies=True, customHeaders={}, chunks=1,
                     resume=False):
        if not referer:
            referer = self.lastURL

        dwnld = HTTPDownload(url, filename, get=get, post=post, referer=referer, cookies=cookies,
                             customHeaders=customHeaders, bucket=self.bucket, interface=self.interface,
                             proxies=self.proxies)
        dwnld.cookieJar = self.cookieJar

        d = dwnld.download(chunks=chunks, resume=resume)
        return d

    def ftpDownload(self, url, filename, resume=False):
        dwnld = FTPDownload(url, filename, bucket=self.bucket, interface=self.interface, proxies=self.proxies)

        d = dwnld.download(resume=resume)
        return d

    def xdccDownload(self, server, port, channel, bot, pack, filename, nick="pyload_%d" % randint(1000, 9999),
                     ident="pyload", real="pyloadreal"):
        dwnld = XDCCDownload(server, port, channel, bot, pack, nick, ident, real, filename, bucket=self.bucket,
                             interface=self.interface, proxies=self.proxies)

        d = dwnld.download()
        return d

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