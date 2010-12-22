#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""

from urllib import urlencode
#from urlparse import urlparse

from urllib2 import Request
from urllib2 import OpenerDirector

from urllib2 import BaseHandler
from urllib2 import HTTPHandler
from urllib2 import HTTPRedirectHandler
from urllib2 import HTTPCookieProcessor
from urllib2 import HTTPSHandler
from urllib2 import HTTPDefaultErrorHandler
from urllib2 import HTTPErrorProcessor
from urllib2 import ProxyHandler

from urllib2 import URLError

from urllib2 import addinfourl
from urllib2 import _parse_proxy

from httplib import HTTPConnection
from httplib import HTTPResponse
from httplib import responses as HTTPStatusCodes
from httplib import ResponseNotReady

from cookielib import CookieJar

import socket
import socks

from MultipartPostHandler import MultipartPostHandler

DEBUG = 0
HANDLE_ERRORS = 1

class PyLoadHTTPResponse(HTTPResponse):
    def __init__(self, sock, debuglevel=0, strict=0, method=None):
        if method: # the httplib in python 2.3 uses the method arg
            HTTPResponse.__init__(self, sock, debuglevel, method)
        else: # 2.2 doesn't
            HTTPResponse.__init__(self, sock, debuglevel)
        self.fileno = sock.fileno
        self._rbuf = ''
        self._rbufsize = 8096
        self._handler = None # inserted by the handler later
        self._host = None    # (same)
        self._url = None     # (same)

    _raw_read = HTTPResponse.read

    def close_connection(self):
        self.close()
        self._handler._remove_connection(self._host, close=1)
        
    def info(self):
        return self.msg

    def geturl(self):
        return self._url

    def read(self, amt=None):
        # the _rbuf test is only in this first if for speed.  It's not
        # logically necessary
        if self._rbuf and not amt is None:
            L = len(self._rbuf)
            if amt > L:
                amt -= L
            else:
                s = self._rbuf[:amt]
                self._rbuf = self._rbuf[amt:]
                return s

        s = self._rbuf + self._raw_read(amt)
        self._rbuf = ''
        return s

    def readline(self, limit=-1):
        i = self._rbuf.find('\n')
        while i < 0 and not (0 < limit <= len(self._rbuf)):
            new = self._raw_read(self._rbufsize)
            if not new: break
            i = new.find('\n')
            if i >= 0: i = i + len(self._rbuf)
            self._rbuf = self._rbuf + new
        if i < 0: i = len(self._rbuf)
        else: i += 1
        if 0 <= limit < len(self._rbuf): i = limit
        data, self._rbuf = self._rbuf[:i], self._rbuf[i:]
        return data

    def readlines(self, sizehint = 0):
        total = 0
        list = []
        while 1:
            line = self.readline()
            if not line: break
            list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return list
    
    @property
    def code(self):
        return self.status
    
    def getcode(self):
        return self.status

class PyLoadHTTPConnection(HTTPConnection):
    sourceAddress = ('', 0)
    socksProxy = None
    response_class = PyLoadHTTPResponse
    
    def connect(self):
        if self.socksProxy:
            self.sock = socks.socksocket()
            t = _parse_proxy(self.socksProxy[1])
            self.sock.setproxy(self.socksProxy[0], addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        else:
            self.sock = socket.socket()
        self.sock.settimeout(30)
        self.sock.bind(self.sourceAddress)
        self.sock.connect((self.host, self.port))
        
        try:
            if self._tunnel_host:
                self._tunnel()
        except: #python2.5
            pass

class PyLoadHTTPHandler(HTTPHandler):
    sourceAddress = ('', 0)
    socksProxy = None
    
    def __init__(self):
        self._connections = {}
    
    def setInterface(self, interface):
        if interface is None:
            interface = ""
        self.sourceAddress = (interface, 0)
    
    def setSocksProxy(self, *t):
        self.socksProxy = t
    
    def close_connection(self, host):
        """close connection to <host>
        host is the host:port spec, as in 'www.cnn.com:8080' as passed in.
        no error occurs if there is no connection to that host."""
        self._remove_connection(host, close=1)

    def open_connections(self):
        """return a list of connected hosts"""
        return self._connections.keys()

    def close_all(self):
        """close all open connections"""
        for host, conn in self._connections.items():
            conn.close()
        self._connections = {}
        
    def _remove_connection(self, host, close=0):
        if self._connections.has_key(host):
            if close: self._connections[host].close()
            del self._connections[host]
        
    def _start_connection(self, h, req):
        data = ""
        try:
            if req.has_data():
                data = req.get_data()
                h.putrequest('POST', req.get_selector())
                if not req.headers.has_key('Content-type'):
                    h.putheader('Content-type',
                                'application/x-www-form-urlencoded')
                if not req.headers.has_key('Content-length'):
                    h.putheader('Content-length', '%d' % len(data))
            else:
                h.putrequest('GET', req.get_selector(), skip_accept_encoding=1)
        except socket.error, err:
            raise URLError(err)

        for args in self.parent.addheaders:
            h.putheader(*args)
        for k, v in req.headers.items():
            h.putheader(k, v)
        h.endheaders()
        if req.has_data():
            h.send(data)

    def do_open(self, http_class, req):
        host = req.get_host()
        if not host:
            raise URLError('no host given')

        need_new_connection = 1
        h = self._connections.get(host)
        if not h is None:
            try:
                self._start_connection(h, req)
            except socket.error, e:
                r = None
            else:
                try: r = h.getresponse()
                except ResponseNotReady, e: r = None

            if r is None or r.version == 9:
                # httplib falls back to assuming HTTP 0.9 if it gets a
                # bad header back.  This is most likely to happen if
                # the socket has been closed by the server since we
                # last used the connection.
                if DEBUG: print "failed to re-use connection to %s" % host
                h.close()
            else:
                if DEBUG: print "re-using connection to %s" % host
                need_new_connection = 0
        if need_new_connection:
            if DEBUG: print "creating new connection to %s" % host
            h = http_class(host)
            h.sourceAddress = self.sourceAddress
            h.socksProxy = self.socksProxy
            self._connections[host] = h
            self._start_connection(h, req)
            r = h.getresponse()

            
        # if not a persistent connection, don't try to reuse it
        if r.will_close: self._remove_connection(host)

        if DEBUG:
            print "STATUS: %s, %s" % (r.status, r.reason)
        r._handler = self
        r._host = host
        r._url = req.get_full_url()

        if r.status in (200, 206) or not HANDLE_ERRORS:
            return r
        else:
            return self.parent.error('http', req, r, r.status, r.reason, r.msg)

    def http_open(self, req):
        return self.do_open(PyLoadHTTPConnection, req)

class NoRedirectHandler(BaseHandler): #supress error
    def http_error_302(self, req, fp, code, msg, headers):
        resp = addinfourl(fp, headers, req.get_full_url())
        resp.code = code
        resp.msg = msg
        return resp

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class HTTPBase():
    def __init__(self, interface=None, proxies={}):
        self.followRedirect = True
        self.interface = interface
        self.proxies = proxies
        
        self.size = None
        
        self.referer = None
        
        self.cookieJar = None
        
        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"
        
        self.handler = PyLoadHTTPHandler()
        self.handler.setInterface(interface)
        if proxies.has_key("socks5"):
            self.handler.setSocksProxy(socks.PROXY_TYPE_SOCKS5, proxies["socks5"])
        elif proxies.has_key("socks4"):
            self.handler.setSocksProxy(socks.PROXY_TYPE_SOCKS4, proxies["socks4"])
        
        self.cookieJar = CookieJar()
        
        self.debug = DEBUG
    
    def createOpener(self, cookies=True):
        opener = OpenerDirector()
        opener.add_handler(self.handler)
        opener.add_handler(MultipartPostHandler())
        opener.add_handler(HTTPSHandler())
        opener.add_handler(HTTPDefaultErrorHandler())
        opener.add_handler(HTTPErrorProcessor())
        if self.proxies.has_key("http") or self.proxies.has_key("https"):
            opener.add_handler(ProxyHandler(self.proxies))
        opener.add_handler(HTTPRedirectHandler() if self.followRedirect else NoRedirectHandler())
        if cookies:
            opener.add_handler(HTTPCookieProcessor(self.cookieJar))
        opener.version = self.userAgent
        opener.addheaders[0] = ("User-Agent", self.userAgent)
        return opener
    
    def createRequest(self, url, get={}, post={}, referer=None, customHeaders={}):
        if get:
            if isinstance(get, dict):
                get = urlencode(get)
            url = "%s?%s" % (url, get)
        
        req = Request(url)
        
        if post:
            if isinstance(post, dict):
                post = urlencode(post)
            req.add_data(post)
        
        req.add_header("Accept", "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5")
        req.add_header("Accept-Language", "en-US,en")

        if referer:
            req.add_header("Referer", referer)
            
        req.add_header("Accept-Encoding", "gzip, deflate")
        for key, val in customHeaders.iteritems():
            req.add_header(key, val)
        
        return req
    
    def getResponse(self, url, get={}, post={}, referer=None, cookies=True, customHeaders={}):
        req = self.createRequest(url, get, post, referer, customHeaders)
        opener = self.createOpener(cookies)
        
        if self.debug:
            print "[HTTP] ----"
            print "[HTTP] creating request"
            print "[HTTP] URL:", url
            print "[HTTP] GET"
            for key, value in get.iteritems(): 
                print "[HTTP] \t", key, ":", value
            if post:
                print "[HTTP] POST"
                for key, value in post.iteritems(): 
                    print "[HTTP] \t", key, ":", value
            print "[HTTP] headers"
            for key, value in opener.addheaders: 
                print "[HTTP] \t", key, ":", value
            for key, value in req.headers.iteritems(): 
                print "[HTTP] \t", key, ":", value
            print "[HTTP] ----"
        
        resp = opener.open(req)
        resp.getcode = lambda: resp.code
        
        if self.debug:
            print "[HTTP] ----"
            print "[HTTP] got response"
            print "[HTTP] status:", resp.getcode()
            print "[HTTP] headers"
            for key, value in resp.info().dict.iteritems(): 
                print "[HTTP] \t", key, ":", value
            print "[HTTP] ----"
        try:
            self.size = int(resp.info()["Content-Length"])
        except: #chunked transfer
            pass
        return resp

if __name__ == "__main__":
    base = HTTPBase()
    resp = base.getResponse("http://python.org/")
    print resp.read()
