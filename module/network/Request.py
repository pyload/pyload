#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
authored by: RaNaN, Spoob
"""
import base64
import cookielib
from gzip import GzipFile
import time
from os import sep, rename, stat
from os.path import exists
import urllib
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
        
        bufferBase = 1024
        bufferMulti = 4
        self.bufferSize = bufferBase*bufferMulti
        self.canContinue = False
        self.offset = 0
        
        self.dl_speed = 0.0
        self.averageSpeed = 0.0
        self.averageSpeeds = []
        self.averageSpeedTime = 0.0
        self.averageSpeedCount = 0.0
        
        self.speedLimitActive = False
        self.maxSpeed = 0
        self.isSlow = False
        
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
        self.pycurl.setopt(pycurl.BUFFERSIZE, self.bufferSize)


        self.pycurl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10")
        self.pycurl.setopt(pycurl.ENCODING, "gzip, deflate")
        self.pycurl.setopt(pycurl.HTTPHEADER, ["Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                           "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                           "Connection: keep-alive",
                           "Keep-Alive: 300"])

    def load(self, url, get={}, post={}, ref=True, cookies=False, just_header=False):

        url = str(url)

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

            if post:
                self.pycurl.setopt(pycurl.POSTFIELDS, post)

            if ref and self.lastURL is not None:
                self.pycurl.setopt(pycurl.REFERER, self.lastURL)

            if just_header:
                self.pycurl.setopt(pycurl.NOPROGRESS, 1)
                self.pycurl.setopt(pycurl.NOBODY, 1)
                self.pycurl.perform()
                self.lastEffectiveURL = self.pycurl.getinfo(pycurl.EFFECTIVE_URL)
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
            
            if not just_header:
                output = rep.read()

            if rep.headers.has_key("content-encoding"):
                if rep.headers["content-encoding"] == "gzip":
                    output = GzipFile('', 'r', 0, StringIO(output)).read()

            self.lastEffectiveURL = rep.geturl()
            self.lastURL = url
            
            if just_header:
                return rep.headers

            return output

    def curl_enable_cookies(self):
        cookie_file = "module" + sep + "cookies.txt"
        self.pycurl.setopt(pycurl.COOKIEFILE, cookie_file)
        self.pycurl.setopt(pycurl.COOKIEJAR, cookie_file)

    def add_auth(self, user, pw):
        
        self.auth = True
        self.user = user
        self.pw = pw
        
        upwstr = str("%s:%s" % (user,pw))
        if self.curl:
            self.pycurl.setopt(pycurl.HTTPHEADER, ['Authorization: Basic ' + base64.encodestring(upwstr)[:-1]])
            self.pycurl.setopt(pycurl.USERPWD, upwstr)
            self.pycurl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_ANY)
        else:
            self.downloader.addheaders.append(['Authorization', 'Basic ' + base64.encodestring(upwstr)[:-1]])

    def add_cookies(self, req):
        cookie_head = ""
        for cookie in self.cookies:
            cookie_head += cookie.name + "=" + cookie.value + "; "
        req.add_header("Cookie", cookie_head)

    def clear_cookies(self):
        if self.curl:
            self.pycurl.setopt(pycurl.COOKIELIST, "")
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

    def download(self, url, file_name, get={}, post={}, ref=True, cookies=False):

        url = str(url)

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
            file_temp = self.get_free_name(file_name) + ".part"
            if not self.canContinue:
                self.fp = open(file_temp, 'wb')
            else:
                self.fp = open(file_temp, 'ab')
            partSize = self.fp.tell()

            self.init_curl()

            self.pycurl.setopt(pycurl.URL, url)
            
            if self.canContinue:
                self.offset = stat(file_temp).st_size
                self.pycurl.setopt(pycurl.RESUME_FROM, self.offset)
                
            self.dl_arrived = self.offset
            
            if cookies:
                self.curl_enable_cookies()

            if post:
                self.pycurl.setopt(pycurl.POSTFIELDS, post)
            
            if self.auth:
                self.add_auth(self.user, self.pw)

            if ref and self.lastURL is not None:
                self.pycurl.setopt(pycurl.REFERER, self.lastURL)

            self.dl_time = time.time()
            self.dl = True
            
            self.chunkSize = 0
            self.chunkRead = 0
            self.subStartTime = 0
            self.maxChunkSize = 0
            
            def restLimit():
                subTime = time.time() - self.subStartTime
                if subTime <= 1:
                    if self.speedLimitActive:
                        return self.maxChunkSize
                    else:
                        return -1
                else:
                    self.updateCurrentSpeed(float(self.chunkRead/1024) / subTime)
                    
                    self.subStartTime = time.time()
                    self.chunkRead = 0
                    if self.maxSpeed > 0:
                        self.maxChunkSize = self.maxSpeed
                    else:
                        self.maxChunkSize = 0
                    return 0

            def writefunc(buf):
                if self.abort:
                    return False
                chunkSize = len(buf)
                while chunkSize > restLimit() > -1:
                    time.sleep(0.05)
                self.maxChunkSize -= chunkSize
                self.fp.write(buf)
                self.chunkRead += chunkSize
                self.dl_arrived += chunkSize
                
            
            self.pycurl.setopt(pycurl.WRITEFUNCTION, writefunc)
            
            try:
                self.pycurl.perform()
            except Exception, e:
                code, msg = e
                if not code == 23:
                    raise Exception, e
                    
            self.fp.close()
            
            if self.abort:
                raise AbortDownload
            
            rename(file_temp, self.get_free_name(file_name))
            
            self.dl = False
            self.dl_finished = time.time()

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
                    
            self.dl = False
            if not self.dl:
                self.dl = True
                file_temp = self.get_free_name(file_name) + ".part"
                file = open(file_temp, 'wb')
                if not self.canContinue:
                    file.truncate()

                conn = self.downloader.open(req, post)
                if conn.headers.has_key("content-length"):
                    self.dl_size = int(conn.headers["content-length"])
                else:
                    self.dl_size = 0
                self.dl_arrived = 0
                self.dl_time = time.time()
                
                chunkSize = 1
                while chunkSize > 0:
                    if self.abort:
                        break
                    chunkRead = 0
                    if not self.speedLimitActive:
                        maxChunkSize = -1
                    elif self.maxSpeed > 0:
                        maxChunkSize = self.maxSpeed
                    else:
                        maxChunkSize = 0
                    subStartTime = time.time()
                    while (time.time() - subStartTime) <= 1:
                        if maxChunkSize == -1 or chunkRead <= maxChunkSize:
                            chunk = conn.read(self.bufferSize)
                            chunkSize = len(chunk)
                            file.write(chunk)
                            self.dl_arrived += chunkSize
                            chunkRead += chunkSize
                        else:
                            time.sleep(0.05)
                    subTime = time.time() - subStartTime
                    self.updateCurrentSpeed(float(chunkRead/1024) / subTime)

                file.close()
                if self.abort:
                    raise AbortDownload
                self.dl = False
                self.dl_finished = time.time()
                rename(file_temp, self.get_free_name(file_name))
                return True
    
    def updateCurrentSpeed(self, speed):
        self.dl_speed = speed
        if self.averageSpeedTime + 10 < time.time():
            self.averageSpeeds = []
            self.averageSpeeds.append(self.averageSpeed)
            self.averageSpeeds.append(speed)
            self.averageSpeed = (speed + self.averageSpeed)/2
            self.averageSpeedTime = time.time()
            self.averageSpeedCount = 2
        else:
            self.averageSpeeds.append(speed)
            self.averageSpeedCount += 1
            allspeed = 0.0
            for s in self.averageSpeeds:
                allspeed += s
            self.averageSpeed = allspeed / self.averageSpeedCount
    
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
            return self.dl_speed
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
        if self.abort:
            return False
        self.dl_arrived = int(dl_d)
        self.dl_size = int(dl_t)

    def get_free_name(self, file_name):
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
        return file_name

if __name__ == "__main__":
    import doctest
    doctest.testmod()
