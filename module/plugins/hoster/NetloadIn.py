#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import tempfile
from time import time
from time import sleep
import hashlib

from module.Plugin import Plugin

class NetloadIn(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "NetloadIn"
        props['type'] = "hoster"
        props['pattern'] = r"http://.*netload\.in/"
        props['version'] = "0.1"
        props['description'] = """Netload.in Download Plugin"""
        props['author_name'] = ("spoob", "RaNaN")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = [None, None, None]
        self.want_reconnect = False
        self.multi_dl = False
        self.api_data = None
        self.init_ocr()
        self.read_config()
        if self.config['premium']:
            self.multi_dl = True
        else:
            self.multi_dl = False

    def prepare(self, thread):
        pyfile = self.parent
        self.req.clear_cookies()
        self.want_reconnect = False


        self.download_api_data()
        if self.file_exists():
            pyfile.status.filename = self.get_file_name()

            if self.config['premium']:
                self.req.load("http://netload.in/index.php", None, { "txtuser" : self.config['username'], "txtpass" : self.config['password'], "txtcheck" : "login", "txtlogin" : ""}, cookies=True)
                self.logger.info("Netload: Use Premium Account")
                pyfile.status.url = self.parent.url
                #@TODO: premium??
                return True

            self.download_html()
            while not pyfile.status.url:
                self.get_wait_time()
                pyfile.status.waituntil = self.time_plus_wait
                pyfile.status.want_reconnect = self.want_reconnect
                thread.wait(self.parent)
                
                pyfile.status.url = self.get_file_url()

        else:
            raise Exception, "The file was not found on the server."
            
    def download_api_data(self):
        url = self.parent.url
        id_regex = re.compile("http://.*netload.in/datei(.*?)(?:\.htm|/)")
        match = id_regex.search(url)
        if match:
            apiurl = "http://netload.in/share/fileinfos2.php"
            src = self.req.load(apiurl, cookies=False, get={"file_id": match.group(1)})
            self.api_data = {}
            if not src == "unknown file_data":
                print "apidata:", src
                lines = src.split(";")
                self.api_data["exists"] = True
                self.api_data["fileid"] = lines[0]
                self.api_data["filename"] = lines[1]
                self.api_data["size"] = lines[2] #@TODO formatting? (ex: '2.07 KB')
                self.api_data["status"] = lines[3]
                self.api_data["checksum"] = lines[4].strip()
            else:
                self.api_data["exists"] = False

    def download_html(self):
        self.html[0] = self.req.load(self.parent.url, cookies=True)
        url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', self.html[0]).group(1).replace("amp;", "")
        for i in range(6):
            self.html[1] = self.req.load(url_captcha_html, cookies=True)
            try:
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', self.html[1]).group(1)
            except:
                url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', self.html[1]).group(1).replace("amp;", "")
                self.html[1] = self.req.load(url_captcha_html, cookies=True)
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', self.html[1]).group(1)

            file_id = re.search('<input name="file_id" type="hidden" value="(.*)" />', self.html[1]).group(1)
            captcha_image = tempfile.NamedTemporaryFile(suffix=".png").name
            self.req.download(captcha_url, captcha_image, cookies=True)
            captcha = self.ocr.get_captcha(captcha_image)
            os.remove(captcha_image)
            self.logger.debug("Captcha %s: %s" % (i, captcha))
            sleep(5)
            self.html[2] = self.req.load("http://netload.in/index.php?id=10", post={"file_id": file_id, "captcha_check": captcha}, cookies=True)

            if re.search(r"(We will prepare your download..|We had a reqeust with the IP)", self.html[2]) != None:
                break

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        try:
            file_url_pattern = r"<a class=\"Orange_Link\" href=\"(http://.+)\" >Click here"
            return re.search(file_url_pattern, self.html[2]).group(1)
        except:
            return None

    def get_wait_time(self):
        if re.search(r"We had a reqeust with the IP", self.html[2]):
            self.want_reconnect = True
            self.time_plus_wait = time() + 10 * 30
            return
            
        wait_seconds = int(re.search(r"countdown\((.+),'change\(\)'\)", self.html[2]).group(1)) / 100
        self.time_plus_wait = time() + wait_seconds
        
    def get_file_name(self):
        if self.api_data["filename"]:
            return self.api_data["filename"]
        elif self.html[0]:
            file_name_pattern = '\t\t\t(.+)<span style="color: #8d8d8d;">'
            file_name_search = re.search(file_name_pattern, self.html[0])
            if file_name_search:
                return file_name_search.group(1)
        return self.parent.url

    def file_exists(self):
        if self.api_data["exists"]:
            return self.api_data["exists"]
        elif self.html[0] and re.search(r"The file has been deleted", self.html[0]) == None:
            return True
        return False

    def proceed(self, url, location):
        self.req.download(url, location, cookies=True)

    def check_file(self, local_file):
        if self.api_data and self.api_data["checksum"]:
            h = hashlib.md5()
            f = open(local_file, "rb")
            h.update(f.read())
            f.close()
            hexd = h.hexdigest()
            if hexd == self.api_data["checksum"]:
                return (True, 0)
            else:
                return (False, 1)
        else:
            return (True, 5)
