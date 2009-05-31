#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
authored by: RaNaN
"""
import urllib
import urllib2
import cookielib
import base64
import time

from Keepalive import HTTPHandler
from cStringIO import StringIO
from gzip import GzipFile

"""
    handles all outgoing HTTP-Requests of the Server
    Usage: create Request Instance
    use retrieveURL and call it with a url at least
    additionaly you can firstly pass the get and secondly the post data in form of a dictonary
    when the last argument is true the handler simulate a http referer with the last called url.
    retrieveUrl returns response as string
    
"""
class Request:
    def __init__(self):

        self.dl_time = 0
        self.dl_finished = 0
        self.dl_size = 0
        self.dl_arrived = 0
        self.dl = False
	
	self.lastURL = None
	self.cj = cookielib.CookieJar()
        handler = HTTPHandler()
	self.opener = urllib2.build_opener(handler, urllib2.HTTPCookieProcessor(self.cj))
	self.downloader = urllib2.build_opener()
	#self.opener.add_handler()
	
	self.opener.addheaders = [
        ("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"),
        ("Accept-Encoding","gzip,deflate"),
        ("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Charset","ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
	("Connection","keep-alive"),
        ("Keep-Alive","300")]

	self.downloader.addheaders = [
        ("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"),
        ("Accept-Encoding","gzip,deflate"),
        ("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Charset","ISO-8859-1,utf-8;q=0.7,*;q=0.7")]
    
    def load(self, url, get = {}, post = {}, ref = True):
	
	if post:
	    post = urllib.urlencode(post)
	else:
	   post = None
	
	if get:
	    get = urllib.urlencode(get)
	else:
	   get = ""
	
	url = url + get
        req = urllib2.Request(url, data = post)
		
	if ref and self.lastURL is not None:
	    req.add_header("Referer",self.lastURL)
	
	rep = self.opener.open(req)
	
	output = rep.read()
				
	if rep.headers.has_key("content-encoding") :
	    if rep.headers["content-encoding"] == "gzip" :
		output = GzipFile('','r',0,StringIO(output)).read()
	
	self.lastURL = url
		
	return output

    def add_auth(self, user, pw):
        self.downloader.addheaders.append(['Authorization','Basic ' + base64.encodestring(user + ':' + pw)[:-1]])


    #def download(url, filename, reporthook = None, data = None): #default von urlretrieve auch None?
     #  return self.downloader.urlretrieve(url, filename, reporthook, data)

    def download(self, url, filename, post = {}):
        
        if post:
            post = urllib.urlencode(post)
        else:
            post = None
            
        if not self.dl:
            self.dl = True
            file = open(filename, 'wb')
            req = urllib2.Request(url, post)
            conn = self.downloader.open(req)
            self.dl_size = int(conn.headers["content-length"])
            self.dl_arrived = 0
            self.dl_time = time.time()
            for chunk in conn:              
                self.dl_arrived += len(chunk)    
                file.write(chunk)
            file.close()
            self.dl = False
            self.dl_finished = time.time()
            return True
     
    def get_speed(self):
        try:
            return (self.dl_arrived / ((time.time() if self.dl else self.dl_finished)  - self.dl_time )) / 1024
        except:
            return 0

    def get_ETA(self):
        try:
            return (self.dl_size - self.dl_arrived) / (self.dl_arrived / (time.time() - self.dl_time)) 
        except:
            return 0

    def kB_left(self):
        return (self.dl_size - self.dl_arrived) / 1024

if __name__ == "__main__" :
    import doctest
    doctest.testmod()
