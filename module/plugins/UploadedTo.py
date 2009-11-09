#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from Plugin import Plugin

class UploadedTo(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "UploadedTo"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www\.)?u(?:p)?l(?:oaded)?\.to/"
        props['version'] = "0.2"
        props['description'] = """Uploaded.to Download Plugin"""
        props['author_name'] = ("spoob", "mkaay")
        props['author_mail'] = ("spoob@pyload.org", "mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = None
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

        while not pyfile.status.url:
        
            self.req.clear_cookies()
            self.download_html()

            pyfile.status.exists = self.file_exists()

            if not pyfile.status.exists:
                raise Exception, "The file was not found on the server."

            pyfile.status.filename = self.get_file_name()
            
            if self.config['premium']:
                pyfile.status.url = self.parent.url
                return True
                
            self.get_waiting_time()

            pyfile.status.waituntil = self.time_plus_wait
            pyfile.status.url = self.get_file_url()
            pyfile.status.want_reconnect = self.want_reconnect

            thread.wait(self.parent)

            pyfile.status.filename = self.get_file_name()

            tries += 1
            if tries > 5:
                raise Exception, "Error while preparing DL, HTML dump: %s" % self.html

        return True
	
    def download_html(self):
        if self.config['premium']:
            self.config['username'], self.config['password']
            self.req.load("http://uploaded.to/login", None, { "email" : self.config['username'], "password" : self.config['password']})
        url = self.parent.url
        self.html = self.req.load(url, cookies=False)

    def get_waiting_time(self):
        try:
            wait_minutes = re.search(r"Or wait ([\d\-]+) minutes", self.html).group(1)
            if int(wait_minutes) < 0: wait_minutes = 1
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            self.time_plus_wait = 0

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.config['premium']:
            self.start_dl = True
            return self.parent.url
            
        try:
            file_url_pattern = r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">"
            return re.search(file_url_pattern, self.html).group(1)
        except:
            return None

    def get_file_name(self):
        try:
            file_name = re.search(r"<td><b>\s+(.+)\s", self.html).group(1)
            file_suffix = re.search(r"</td><td>(\..+)</td></tr>", self.html)
            if not file_suffix:
                return file_name
            return file_name + file_suffix.group(1)
        except:
            self.parent.status.url = None
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if re.search(r"(File doesn't exist .*)", self.html) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
    	if self.config['premium']:
        	self.req.download(url, location, cookies=True)
        else:
        	self.req.download(url, location, cookies=False, post={"download_submit": "Free Download"})
