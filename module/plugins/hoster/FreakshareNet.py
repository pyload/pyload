#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
import httplib
from module.plugins.Hoster import Hoster
from time import time


class FreakshareNet(Hoster):
    __name__ = "FreakshareNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?freakshare\.net/files/\S*?/"
    __version__ = "0.1"
    __description__ = """Freakshare.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay")
    __author_mail__ = ("sitacuisses@yahoo.de","spoob@pyload.org","mkaay@mkaay.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.want_reconnect = False
        self.multi_dl = False
        self.req_opts = list()
    
    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False
        
        self.download_html()
        
        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            return False
            
        self.get_waiting_time()

        pyfile.status.filename = self.get_file_name()
            
        pyfile.status.waituntil = self.time_plus_wait
        thread.wait(self.parent)
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect

        return True

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            self.req_opts = self.get_download_options() # get the Post options for the Request
            file_url = self.parent.url
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search(r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center\;\">(.*?)<\/h1>", self.html).group(1)
            return file_name
        else:
            return self.parent.url
    
    def get_waiting_time(self):
        if self.html == None:
            self.download_html()
        timestring = re.search('\s*var\stime\s=\s(\d*?)\.\d*;', self.html).group(1)
        if timestring:
            sec = int(timestring) + 1 #add 1 sec as tenths of seconds are cut off
        else:
            sec = 0
        self.time_plus_wait = time() + sec

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"Sorry, this Download doesnt exist anymore", self.html) != None:
            return False
        else:
            return True

    def get_download_options(self):
        re_envelope = re.search(r".*?value=\"Free\sDownload\".*?\n*?(.*?<.*?>\n*)*?\n*\s*?</form>", self.html).group(0) #get the whole request
        to_sort = re.findall(r"<input\stype=\"hidden\"\svalue=\"(.*?)\"\sname=\"(.*?)\"\s\/>", re_envelope)
        request_options = list()
        for item in to_sort:       #Name value pairs are output reversed from regex, so we reorder them
         request_options.append((item[1], item[0]))
        herewego = self.load(self.parent.url, None, request_options, cookies=True) # the actual download-Page
        to_sort = None
        to_sort = re.findall(r"<input\stype=\".*?\"\svalue=\"(\S*?)\".*?name=\"(\S*?)\"\s.*?\/>", herewego)
        request_options = list()
        for item in to_sort:       #Same as above
         request_options.append((item[1], item[0]))
        return request_options

    def proceed(self, url, location):
        """
        request.download doesn't handle the 302 redirect correctly
        that's why the data are posted "manually" via httplib
        and the redirect-url is read from the header.
        Important: The cookies may not be posted to the download-url
        otherwise the downloaded file only contains "bad try"
        Need to come up with a better idea to handle the redirect,
        help is appreciated.
        """
        temp_options = urllib.urlencode(self.req_opts)
        temp_url = re.match(r"http://(.*?)/.*", url).group(1) # get the server name
        temp_extended = re.match(r"http://.*?(/.*)", url).group(1) # get the url relative to serverroot
        cookie_list = ""
        for temp_cookie in self.req.cookies: #prepare cookies
         cookie_list += temp_cookie.name + "=" + temp_cookie.value +";"
        temp_headers = [  #create the additional header fields
        ["Content-type", "application/x-www-form-urlencoded"], #this is very important
        ["User-Agent", "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.10"],
        ["Accept-Encoding", "deflate"],
        ["Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"],
        ["Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7"],
        ["Connection", "keep-alive"],
        ["Keep-Alive", "300"],
        ["Referer", self.req.lastURL],
        ["Cookie", cookie_list]]
        temp_conn = httplib.HTTPConnection(temp_url)
        temp_conn.request("POST", temp_extended, temp_options, dict(temp_headers))
        temp_response = temp_conn.getresponse()
        new_url = temp_response.getheader("Location") # we need the Location-header
        temp_conn.close
        self.download(new_url, location, cookies=False)
