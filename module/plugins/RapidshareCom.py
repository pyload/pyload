#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time

from Plugin import Plugin
import hashlib

class RapidshareCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RapidshareCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www\.)?(?:rs\d*\.)?rapidshare.com/files/(\d*?)/(.*)"
        props['version'] = "0.5"
        props['description'] = """Rapidshare.com Download Plugin"""
        props['author_name'] = ("spoob", "RaNaN", "mkaay")
        props['author_mail'] = ("spoob@pyload.org", "ranan@pyload.org", "mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = [None, None]
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.want_reconnect = False
        self.read_config()
        if self.config['premium']:
            self.multi_dl = True
        else:
            self.multi_dl = False

        self.start_dl = False

    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False

        tries = 0
        
        while not self.start_dl or not pyfile.status.url:

            self.req.clear_cookies()

            self.download_html()

            pyfile.status.exists = self.file_exists()
            
            if not pyfile.status.exists:
                raise Exception, "The file was not found on the server."
            
            self.download_api_data()
            
            pyfile.status.filename = self.get_file_name()
            
            if self.config['premium']:
                pyfile.status.url = self.parent.url
                return True

            self.download_serverhtml()
            pyfile.status.waituntil = self.time_plus_wait
            pyfile.status.want_reconnect = self.want_reconnect

            thread.wait(self.parent)

            pyfile.status.url = self.get_file_url()

            tries += 1
            if tries > 5:
                raise Exception, "Error while preparing, HTML dump:"+ str(self.html[0]) + str(self.html[1])

        return True

    def download_api_data(self):
        """
        http://images.rapidshare.com/apidoc.txt
        """
        url = self.parent.url
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param = {"sub": "checkfiles_v1", "files": "", "filenames": "", "incmd5": "1"}
        m = re.compile(self.props['pattern']).search(url)
        if m:
            api_param["files"] = m.group(1)
            api_param["filenames"] = m.group(2)
            src = self.req.load(api_url_base, cookies=False, get=api_param)
            if not src.find("ERROR"):
                return
            fields = src.split(",")
            self.api_data = {}
            self.api_data["fileid"] = fields[0]
            self.api_data["filename"] = fields[1]
            self.api_data["size"] = fields[2] # in bytes
            self.api_data["serverid"] = fields[3]
            self.api_data["status"] = fields[4]
            """
            status codes:
                0=File not found
                1=File OK (Downloading possible without any logging)
                2=File OK (TrafficShare direct download without any logging)
                3=Server down
                4=File marked as illegal
                5=Anonymous file locked, because it has more than 10 downloads already
                6=File OK (TrafficShare direct download with enabled logging)
            """
            self.api_data["shorthost"] = fields[5]
            self.api_data["checksum"] = fields[6].strip().lower() # md5
            
            self.api_data["mirror"] = "http://rs%(serverid)s%(shorthost)s.rapidshare.com/files/%(fileid)s/%(filename)s" % self.api_data

    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """
        url = self.parent.url
        self.html[0] = self.req.load(url)
        self.html_old = time()

    def download_serverhtml(self):
        """downloads html with the important informations
        """
        file_server_url = re.search(r"<form action=\"(.*?)\"", self.html[0]).group(1)
        self.html[1] = self.req.load(file_server_url, None, {"dl.start": "Free"})
        self.html_old = time()
        self.get_wait_time()

    def get_wait_time(self):
        if re.search(r"is already downloading", self.html[1]) != None:
            self.time_plus_wait = time() + 10 * 60
        try:
            wait_minutes = re.search(r"Or try again in about (\d+) minute", self.html[1]).group(1)
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            if re.search(r"(Currently a lot of users|There are no more download slots)", self.html[1], re.I) != None:
                self.time_plus_wait = time() + 130
                return True
            wait_seconds = re.search(r"var c=(.*);.*", self.html[1]).group(1)
            self.time_plus_wait = time() + int(wait_seconds) + 5

    def file_exists(self):
        """ returns True or False
        """
        if re.search("The file could not be found|This limit is reached| \
            is momentarily not available|removed this file| \
            contain illegal content", self.html[0], re.I) != None:
            return False
        else:
            return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.config['premium']:
            self.start_dl = True
            if self.api_data and self.api_data["mirror"]:
                return self.api_data["mirror"]
            return self.parent.url

        #if (self.html_old + 5 * 60) < time(): # nach einiger zeit ist die file_url nicht mehr aktuell
        #   self.download_serverhtml()

        try:
            if self.api_data and self.api_data["mirror"]:
                return self.api_data["mirror"]
            if self.config['server'] == "":
                file_url_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
            else:
                file_url_pattern = '(http://rs.*)\';" /> %s<br />' % self.config['server']

            self.start_dl = True
            return re.search(file_url_pattern, self.html[1]).group(1)
        except Exception, e:
            self.start_dl = False
            return False
            #print self.html[1] #test print
            #raise Exception, "Error when retrieving download url"

    def get_file_name(self):
        if self.api_data and self.api_data["filename"]:
            return self.api_data["filename"]
        file_name_pattern = r"<p class=\"downloadlink\">.+/(.+) <font"
        return re.findall(file_name_pattern, self.html[0])[0]

    def proceed(self, url, location):
        if self.config['premium']:
            self.req.add_auth(self.config['username'], self.config['password'])
        self.req.download(url, location)

    def check_file(self, local_file):
        if self.api_data and self.api_data["checksum"]:
            h = hashlib.md5()
            with open(local_file, "rb") as f:
                h.update(f.read())
            hexd = h.hexdigest()
            if hexd == self.api_data["checksum"]:
                return (True, 0)
            else:
                return (False, 1)
        else:
        	return (True, 5)
