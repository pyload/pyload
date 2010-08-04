#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time
from time import sleep
import hashlib

from module.plugins.Hoster import Hoster
from module.plugins.Plugin import Plugin

class NetloadIn(Hoster):
    __name__ = "NetloadIn"
    __type__ = "hoster"
    __pattern__ = r"http://.*netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)"
    __version__ = "0.2"
    __description__ = """Netload.in Download Hoster"""
    __author_name__ = ("spoob", "RaNaN")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org")

    def setup(self):
        self.multiDL = False
    
    def process(self, pyfile):
        self.html = [None, None, None]
        self.url = pyfile.url
        self.prepare()
        self.pyfile.setStatus("downloading")
        self.proceed(self.url)
    
    def prepare(self):
        self.download_api_data()
        if self.file_exists():
            self.pyfile.name = self.get_file_name()

            #if self.config['premium']:
            #    self.log.info("Netload: Use Premium Account")
            #    return True
                    
            for i in range(5):
                if not self.download_html():
                    self.setWait(5)     
                    self.log.info(_("Netload: waiting %d minutes, because the file is currently not available." % self.get_wait_time()))
                    self.wait()
                    continue
            
                wait_time = self.get_wait_time()
                self.setWait(wait_time)
                self.log.debug(_("Netload: waiting %d seconds" % wait_time))
                self.wait()
                
                self.url = self.get_file_url()
                return True

        else:
            self.offline()
            
    def download_api_data(self):
        url = self.url
        id_regex = re.compile("http://.*netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)")
        match = id_regex.search(url)
        if match:
            apiurl = "http://netload.in/share/fileinfos2.php"
            src = self.load(apiurl, cookies=False, get={"file_id": match.group(1)})
            self.api_data = {}
            if src == "unknown_server_data":
                self.api_data = False
                self.html[0] = self.load(self.url, cookies=False)
            elif not src == "unknown file_data":
                lines = src.split(";")
                self.api_data["exists"] = True
                self.api_data["fileid"] = lines[0]
                self.api_data["filename"] = lines[1]
                self.api_data["size"] = lines[2] #@TODO formatting? (ex: '2.07 KB')
                self.api_data["status"] = lines[3]
                self.api_data["checksum"] = lines[4].strip()
            else:
                self.api_data["exists"] = False
        else:
            self.api_data = False
            self.html[0] = self.load(self.url, cookies=False)

    def download_html(self):
        self.html[0] = self.load(self.url, cookies=True)
        url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', self.html[0]).group(1).replace("amp;", "")
        
        m = re.search(r"countdown\((\d+),'change\(\)'\);", url_captcha_html)
        if m:
            wait_time = int(m.group(1))
            self.log.debug(_("Netload: waiting %d seconds." % wait_time))
            self.setWait(wait_time)
            self.wait()

        for i in range(6):
            self.html[1] = self.load(url_captcha_html, cookies=True)
            if "Please retry again in a few minutes" in self.html[1]:
                return False
            
            try:
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', self.html[1]).group(1)
            except:
                open("dump.html", "w").write(self.html[1])
                url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', self.html[1]).group(1).replace("amp;", "")
                self.html[1] = self.load(url_captcha_html, cookies=True)
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', self.html[1]).group(1)

            file_id = re.search('<input name="file_id" type="hidden" value="(.*)" />', self.html[1]).group(1)
            
            captcha = self.decryptCaptcha(captcha_url)
            sleep(5)
            
            self.html[2] = self.load("http://netload.in/index.php?id=10", post={"file_id": file_id, "captcha_check": captcha}, cookies=True)

            if re.search(r"(We will prepare your download..|We had a reqeust with the IP)", self.html[2]) != None:
                return True
        
        self.fail("Captcha not decrypted")

    def get_file_url(self):
        try:
            file_url_pattern = r"<a class=\"Orange_Link\" href=\"(http://.+)\" >Click here"
            return re.search(file_url_pattern, self.html[2]).group(1)
        except:
            return None

    def get_wait_time(self):
        if re.search(r"We had a request with the IP", self.html[2]):
            wait_minutes = int(re.search(r"countdown\((.+),'change\(\)'\)", self.html[2]).group(1)) / 6000
            self.wantReconnect = True
            return wait_minutes * 60
            
        wait_seconds = int(re.search(r"countdown\((.+),'change\(\)'\)", self.html[2]).group(1)) / 100
        return wait_seconds
        
    def get_file_name(self):
        if self.api_data and self.api_data["filename"]:
            return self.api_data["filename"]
        elif self.html[0]:
            file_name_pattern = '\t\t\t(.+)<span style="color: #8d8d8d;">'
            file_name_search = re.search(file_name_pattern, self.html[0])
            if file_name_search:
                return file_name_search.group(1)
        return self.url

    def file_exists(self):
        if self.api_data and self.api_data["exists"]:
            return self.api_data["exists"]
        elif self.html[0] and re.search(r"The file has been deleted", self.html[0]) == None:
            return True
        return False

    def proceed(self, url):
        #if self.config['premium']:
        #    self.req.load("http://netload.in/index.php", None, { "txtuser" : self.config['username'], "txtpass" : self.config['password'], "txtcheck" : "login", "txtlogin" : ""}, cookies=True)
        self.download(url, cookies=True)

