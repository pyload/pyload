#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
authored by: RaNaN, Spoob
"""
import os
import base64
import cookielib
from gzip import GzipFile
import time
import re
from os import sep, rename
from os.path import dirname, exists
import urllib
from base64 import b64decode
from cStringIO import StringIO

try:
    import pycurl
except:
    import urllib2
    from Keepalive import HTTPHandler


"""
    handles all outgoing HTTP-Requests of the Server
    Usage: create Request Instance
    use retrieveURL and call it with a url at least
    additionaly you can firstly pass the get and secondly the post data in form of a dictonary
    when the last argument is true the handler simulate a http referer with the last called url.
    retrieveUrl returns response as string

"""
class AbortDownload(Exception):
    pass

class Request:
    def __init__(self):

        self.dl_time = 0
        self.dl_finished = 0
        self.dl_size = 0
        self.dl_arrived = 0
        self.dl = False

        self.abort = False

        self.lastEffectiveURL = None
        self.lastURL = None
        self.auth = False
        
        self.timeout = 5

        try:
            if pycurl: self.curl = True
        except:
            self.curl = False

        if self.curl:

            self.init_curl()

        else:
            self.cookies = []
            self.cj = cookielib.CookieJar()
            handler = HTTPHandler()
            self.opener = urllib2.build_opener(handler, urllib2.HTTPCookieProcessor(self.cj))
            self.downloader = urllib2.build_opener()
            #self.opener.add_handler()

            self.opener.addheaders = [
            ("User-Agent", "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"),
            ("Accept-Encoding", "deflate"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
            ("Connection", "keep-alive"),
            ("Keep-Alive", "300")]

            self.downloader.addheaders = [
            ("User-Agent", "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"),
            ("Accept-Encoding", "deflate"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7")]

    def set_timeout(self, timeout):
        self.timeout = int(timeout)

    def init_curl(self):
        self.rep = StringIO()
        self.header = ""

        self.pycurl = pycurl.Curl()
        self.pycurl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.pycurl.setopt(pycurl.MAXREDIRS, 5)
        self.pycurl.setopt(pycurl.TIMEOUT, (self.timeout*3600))
        self.pycurl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.pycurl.setopt(pycurl.NOSIGNAL, 1)
        self.pycurl.setopt(pycurl.NOPROGRESS, 0)
        self.pycurl.setopt(pycurl.PROGRESSFUNCTION, self.progress)
        self.pycurl.setopt(pycurl.AUTOREFERER, 1)
        self.pycurl.setopt(pycurl.HEADERFUNCTION, self.write_header)


        self.pycurl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10")
        self.pycurl.setopt(pycurl.ENCODING, "gzip, deflate")
        self.pycurl.setopt(pycurl.HTTPHEADER, ["Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                           "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                           "Connection: keep-alive",
                           "Keep-Alive: 300"])

    def load(self, url, get={}, post={}, ref=True, cookies=False, just_header=False):

        if post:
            post = urllib.urlencode(post)
        else:
            post = None

        if get:
            get = urllib.urlencode(get)
            url = "%s?%s" % (url, get)
        else:
            get = ""

        if self.curl:
            
            self.pycurl.setopt(pycurl.URL, url)
            self.pycurl.setopt(pycurl.WRITEFUNCTION, self.rep.write)
            
            if cookies:
                self.curl_enable_cookies()

            if post: self.pycurl.setopt(pycurl.POSTFIELDS, post)

            if ref and self.lastURL is not None:
                self.pycurl.setopt(pycurl.REFERER, self.lastURL)

            if just_header:
                self.pycurl.setopt(pycurl.NOPROGRESS, 1)
                self.pycurl.setopt(pycurl.NOBODY, 1)
                self.pycurl.perform()
                self.pycurl.setopt(pycurl.NOPROGRESS, 0)
                self.pycurl.setopt(pycurl.NOBODY, 0)
                return self.header

            self.pycurl.perform()

            self.lastEffectiveURL = self.pycurl.getinfo(pycurl.EFFECTIVE_URL)
            self.lastURL = url
            header = self.get_header()

            return self.get_rep()


        else:
            req = urllib2.Request(url, data=post)

            if ref and self.lastURL is not None:
                req.add_header("Referer", self.lastURL)

            if cookies:
                self.add_cookies(req)
                #add cookies

            rep = self.opener.open(req)

            for cookie in self.cj.make_cookies(rep, req):
                self.cookies.append(cookie)

            output = rep.read()

            if rep.headers.has_key("content-encoding"):
                if rep.headers["content-encoding"] == "gzip":
                    output = GzipFile('', 'r', 0, StringIO(output)).read()

            self.lastEffectiveURL = rep.geturl()
            self.lastURL = url

            return output

    def curl_enable_cookies(self):
        cookie_file = "module" + sep + "cookies.txt"
        self.pycurl.setopt(pycurl.COOKIEFILE, cookie_file)
        self.pycurl.setopt(pycurl.COOKIEJAR, cookie_file)

    def add_auth(self, user, pw):
        
        self.auth = True
        self.user = user
        self.pw = pw

        if self.curl:
            self.pycurl.setopt(pycurl.HTTPHEADER, ['Authorization: Basic ' + base64.encodestring(user + ':' + pw)[:-1]])
            self.pycurl.setopt(pycurl.USERPWD, user + ":" + pw)
            self.pycurl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_ANY)
        else:
            self.downloader.addheaders.append(['Authorization', 'Basic ' + base64.encodestring(user + ':' + pw)[:-1]])

    def add_cookies(self, req):
        cookie_head = ""
        for cookie in self.cookies:
            cookie_head += cookie.name + "=" + cookie.value + "; "
        req.add_header("Cookie", cookie_head)
    #def download(url, filename, reporthook = None, data = None): #default von urlretrieve auch None?
        #  return self.downloader.urlretrieve(url, filename, reporthook, data)

    def clear_cookies(self):
        if self.curl:
            self.pycurl.setopt(pycurl.COOKIELIST, "ALL")
        else:
            del self.cookies[:]

    def add_proxy(self, protocol, adress):

        # @TODO: pycurl proxy protocoll selection
        if self.curl:
            self.pycurl.setopt(pycurl.PROXY, adress.split(":")[0])
            self.pycurl.setopt(pycurl.PROXYPORT, adress.split(":")[1])
        else:
            handler = urllib2.ProxyHandler({protocol: adress})
            self.opener.add_handler(handler)
            self.downloader.add_handler(handler)

    def download(self, url, file_name, folder="", get={}, post={}, ref=True, cookies=False):

        if post:
            post = urllib.urlencode(post)
        else:
            post = None

        if get:
            get = urllib.urlencode(get)
            url = "%s?%s" % (url, get)
        else:
            get = ""

        if self.curl:

            file_temp = file_name + ".part"
            fp = open(file_temp, 'wb')

            self.init_curl()

            self.pycurl.setopt(pycurl.URL, url)
            self.pycurl.setopt(pycurl.WRITEDATA, fp)
            
            if cookies:
                self.curl_enable_cookies()

            if post: self.pycurl.setopt(pycurl.POSTFIELDS, post)
            
            if self.auth:
                self.add_auth(self.user, self.pw)

            if ref and self.lastURL is not None:
                self.pycurl.setopt(pycurl.REFERER, self.lastURL)

            self.dl_arrived = 0
            self.dl_time = time.time()
            self.dl = True

            self.pycurl.perform()
            if "..." in file_name:
                download_folder = dirname(file_name) + sep
                headers = self.get_header()
                file_name_search = re.search('filename=(?P<quote>\")?(.+)(?(quote)\")', headers)
                if file_name_search:
                    file_name = file_name_search.group(2)
                    if "?=" in file_name[-3:]:
                        file_name = file_name.replace("=?UTF-8?B?", "").replace("?=", "==")
                        file_name = b64decode(file_name)
                    file_name = download_folder + sep + file_name
                        
            file_count = 0
            while exists(file_name):
                file_count += 1
                if "." in file_name:
                    file_split = file_name.split(".")
                    temp_name = "%s-%i.%s" % (".".join(file_split[:-1]), file_count, file_split[-1])
                else:
                    temp_name = "%s-%i" % (file_name, file_count)
                if not exists(temp_name):
                    file_name = temp_name
                    
            rename(file_temp, file_name)

            self.dl = False
            self.dl_finished = time.time()

            fp.close()

            return True

        else:

            req = urllib2.Request(url, data=post)

            if ref and self.lastURL is not None:
                req.add_header("Referer", self.lastURL)

            if cookies:
                self.add_cookies(req)
                #add cookies
                rep = self.opener.open(req)

                for cookie in self.cj.make_cookies(rep, req):
                    self.cookies.append(cookie)

            if not self.dl:
                self.dl = True
                file = open(file_name, 'wb')

                conn = self.downloader.open(req, post)
                if conn.headers.has_key("content-length"):
                    self.dl_size = int(conn.headers["content-length"])
                else:
                    self.dl_size = 0
                self.dl_arrived = 0
                self.dl_time = time.time()
                for chunk in conn:
                    if self.abort: raise AbortDownload
                    self.dl_arrived += len(chunk)
                    file.write(chunk)

                file.close()
                self.dl = False
                self.dl_finished = time.time()
                return True

    def write_header(self, string):
        self.header += string

    def get_rep(self):
        value = self.rep.getvalue()
        self.rep.close()
        self.rep = StringIO()
        return value
    
    def get_header(self):
        h = self.header
        self.header = ""
        return h

    def get_speed(self):
        try:
            return (self.dl_arrived / ((time.time() if self.dl else self.dl_finished)  - self.dl_time)) / 1024
        except:
            return 0

    def get_ETA(self):
        try:
            return (self.dl_size - self.dl_arrived) / (self.dl_arrived / (time.time() - self.dl_time))
        except:
            return 0

    def kB_left(self):
        return (self.dl_size - self.dl_arrived) / 1024
    
    def progress(self, dl_t, dl_d, up_t, up_d):
        if self.abort: raise AbortDownload
        self.dl_arrived = int(dl_d)
        self.dl_size = int(dl_t)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
