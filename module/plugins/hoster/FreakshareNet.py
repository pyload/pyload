#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

class FreakshareNet(Hoster):
    __name__ = "FreakshareNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?freakshare\.net/files/\S*?/"
    __version__ = "0.32"
    __description__ = """Freakshare.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay")
    __author_mail__ = ("sitacuisses@yahoo.de","spoob@pyload.org","mkaay@mkaay.de")

    def setup(self):
        self.html = None
        self.wantReconnect = False
        self.multiDL = False
        self.req_opts = []

    def process(self, pyfile):
        self.pyfile = pyfile
        self.prepare()
        self.get_file_url()

        self.download(self.pyfile.url, post=self.req_opts)
        
    
    def prepare(self):
        pyfile = self.pyfile

        self.wantReconnect = False
        
        self.download_html()

        if not self.file_exists():
            self.offline()
            
        self.setWait( self.get_waiting_time() )

        pyfile.name = self.get_file_name()
            
        self.wait()

        return True

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()
        if not self.wantReconnect:
            self.req_opts = self.get_download_options() # get the Post options for the Request
            #file_url = self.pyfile.url
            #return file_url
        else:
            self.offline()

    def get_file_name(self):
        if self.html is None:
            self.download_html()
        if not self.wantReconnect:
            file_name = re.search(r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center\;\">([^ ]+)", self.html).group(1)
            return file_name
        else:
            return self.pyfile.url
    
    def get_waiting_time(self):
        if self.html is None:
            self.download_html()
            
        if "Der Traffic f\xc3\xbcr heute ist verbraucht!" in self.html or "Your Traffic is used up for today" in self.html:
            self.wantReconnect = True
            return 24*3600
            
        timestring = re.search('\s*var\stime\s=\s(\d*?)\.\d*;', self.html).group(1)
        if timestring:
            sec = int(timestring) + 1 #add 1 sec as tenths of seconds are cut off
        else:
            sec = 0
        return sec

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        if re.search(r"Sorry, this Download doesnt exist anymore", self.html) is not None:
            return False
        else:
            return True

    def get_download_options(self):
        re_envelope = re.search(r".*?value=\"Free\sDownload\".*?\n*?(.*?<.*?>\n*)*?\n*\s*?</form>", self.html).group(0) #get the whole request
        to_sort = re.findall(r"<input\stype=\"hidden\"\svalue=\"(.*?)\"\sname=\"(.*?)\"\s\/>", re_envelope)
        request_options = []
        
        for item in to_sort:       #Name value pairs are output reversed from regex, so we reorder them
            request_options.append((item[1], item[0]))
            
        herewego = self.load(self.pyfile.url, None, request_options, cookies=True) # the actual download-Page
        
        to_sort = re.findall(r"<input\stype=\".*?\"\svalue=\"(\S*?)\".*?name=\"(\S*?)\"\s.*?\/>", herewego)
        request_options = []
        
        for item in to_sort:       #Same as above
            request_options.append((item[1], item[0]))

        challenge = re.search(r"http://api\.recaptcha\.net/challenge\?k=([0-9A-Za-z]+)", herewego)

        if challenge:
            re_captcha = ReCaptcha(self)
            challenge, result = re_captcha.challenge(challenge.group(1))

            request_options.append(("recaptcha_challenge_field", challenge))
            request_options.append(("recaptcha_response_field", result))

        return request_options