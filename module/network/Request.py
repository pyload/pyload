#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
authored by: RaNaN
"""
import urllib
import urllib2
import cookielib
import Keepalive

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
class Downloader(urllib.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8"



class Request:
    def __init__(self):
	
	self.lastURL = None
	#self.cookiefile = 'cookies.lwp'
	self.cj = cookielib.CookieJar()

#	if os.path.isfile(self.cookiefile):
 #           self.cj.load(self.cookiefile)

        self.handler = HTTPHandler()
	self.opener = urllib2.build_opener(self.handler, urllib2.HTTPCookieProcessor(self.cj))
	#self.opener.add_handler()
	
	self.opener.addheaders = [
        ("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8"),
        ("Accept-Encoding","gzip,deflate"),
        ("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Charset","ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
	("Connection","keep-alive"),
        ("Keep-Alive","300")]
	
	self.downloader = Downloader()
	
    
    def retrieveURL(self,url, get = {}, post = {}, ref = True):
	
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
	
	print rep.headers
		
	self.cj.extract_cookies(rep, req)
	
	if rep.headers.has_key("content-encoding") :
	    if rep.headers["content-encoding"] == "gzip" :
		output = GzipFile('','r',0,StringIO(output)).read()
	
	self.lastURL = url
		
	return output

    def addAuth(self, user, pw):
        auth_handler = urllib2.HTTPBasicAuthHandler()
	auth_handler.add_password(user, passwd= pw)
	self.opener.add_handler(auth_handler)

    def download(url, filename, reporthook = None, data = None): #default von urlretrieve auch None?
       return self.downloader.urlretrieve(url, filename, reporthook, data)


if __name__ == "__main__" :
    import doctest
    doctest.testmod()
