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
    
    @author: spoob
    @author: RaNaN
    @author: mkaay
"""

import time
from os.path import exists, join
from shutil import move
import urllib

from module.plugins.Plugin import Abort

from module.network.Browser import Browser
from module.network.helper import waitFor

class Request(object):
    def __init__(self, interface=None):
        self.browser = Browser(interface=interface)
        self.d = None
        
        self.dl_time = 0
        self.dl_finished = 0
        self.dl_size = 0
        self.dl_arrived = 0
        self.dl = False

        self.abort = False

        self.lastEffectiveURL = self.lastURL = property(lambda: self.browser.lastUrl)
        self.auth = False
        
        self.canContinue = False
        
        self.dl_speed = 0.0
        
        self.cookieJar = None
        self.interface = interface
        self.progressNotify = None
        
        # change this for connection information
        self.debug = False

    def set_timeout(self, timeout):
        self.timeout = int(timeout)
    
    def setCookieJar(self, j):
        #self.cookieJar = j
        pass
    
    def addCookies(self):
        #@TODO
        pass
    
    def getCookies(self):
        #@TODO
        pass
    
    def getCookie(self, name):
        #@TODO
        pass
    
    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, no_post_encode=False, raw_cookies={}):
        url = self.__myquote(str(url))
        
        #@TODO: cookies
        #@TODO: auth
        
        if not ref:
            self.browser.clearReferer()

        return self.browser.getPage(url, get=get, post=post, cookies=cookies)

    def add_auth(self, user, pw):
        #@TODO
        pass

    def clearCookies(self):
        #@TODO
        pass

    def add_proxy(self, protocol, adress):
        #@TODO
        pass

    def download(self, url, file_name, folder, get={}, post={}, ref=True, cookies=True, no_post_encode=False):
        url = self.__myquote(str(url))
        
        file_temp = self.get_free_name(folder,file_name)
      
        #@TODO: cookies
        #@TODO: auth
        
        if not ref:
            self.browser.clearReferer()
        
        self.d = self.browser.httpDownload(url, file_temp, get=get, post=post, cookies=cookies, chunks=1, resume=self.canContinue)
        
        waitFor(self.d)
        
        if self.abort: raise Abort

        free_name = self.get_free_name(folder, file_name)
        move(file_temp, free_name)
        
        self.dl_time = 0
        self.dl_finished = 0
        self.dl_size = 0
        self.dl_arrived = 0
        self.dl = False
        self.dl_speed = 0.0
        
        return free_name

    dl_time = property(lambda self: self.d.startTime)
    dl_finished = property(lambda self: self.d.endTime)
    dl_speed = property(lambda self: self.d.speed)
    dl_size = property(lambda self: self.d.size)
    dl = property(lambda self: True if self.d.startTime and not self.d.endTime else False)
    abort = property(lambda self: self.d.getAbort, lambda self, value: self.d.setAbort(value))

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

    def bytes_left(self):
        return (self.dl_size - self.dl_arrived)
    
    def progress(self):
        if self.progressNotify:
            try:
                progress = int(float(self.dl_arrived)/self.dl_size*100)
                self.progressNotify(progress)
            except:
                pass
        
    def get_free_name(self, folder, file_name):
        file_count = 0
        file_name = join(folder, file_name)
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
            
    def __myquote(self, url):
        return urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")


def getURL(url, get={}, post={}):
    """
        currently used for update check
    """
    b = Browser()
    return b.getPage(url, get=get, post=post)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
