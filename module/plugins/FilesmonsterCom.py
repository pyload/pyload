#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Plugin for www.filesmonster.com
# this plugin isn't fully implemented yet,but it does download
# todo:
# detect, if reconnect is necessary
# download-error handling
# postpone download, if speed is below a set limit
# implement premium-access
# optional replace blanks in filename with underscores

import re
import urllib
import time
from Plugin import Plugin

class FilesmonsterCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "FilesmonsterCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(www.)??filesmonster.com/download.php"
        props['version'] = "0.1"
        props['description'] = """Filesmonster.com Download Plugin"""
        props['author_name'] = ("sitacuisses","spoob")
        props['author_mail'] = ("sitacuisses@yahoo.de","spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.want_reconnect = False
        self.multi_dl = False
        self.htmlwithlink = None
        self.url = None
        self.filerequest = None

    def download_html(self):
        self.url = self.parent.url
        self.html = self.req.load(self.url) # get the start page

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            self.get_download_page() # the complex work is done here
            file_url = self.htmlwithlink
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search(r"File\sname:\s<span\sclass=\"em\">(.*?)</span>", self.html).group(1)
            return file_name
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights.", self.html) != None:
            return False
        else:
            return True

    def get_download_page(self):
     herewego = re.findall(r"<form\sid=\'slowdownload\'\smethod=\"post\"\saction=\"http://filesmonster.com/get/free/\">\s*\n\s*<input\stype=\"hidden\"\sname=\"(\S*?)\"\svalue=\"(\S*?)\"\s*>", self.html)
     the_download_page = self.req.load("http://filesmonster.com/get/free/", None, herewego)
     temporary_filtered = re.search(r"</div><form\sid=\'rtForm\'\sname=\"rtForm\"\smethod=\"post\">\s*\n(\s*<input\stype=\'hidden\'\sname=\'(\S*?)\'\svalue=\'(\S*?)\'>\s*\n)*?\s*</form>", the_download_page).group(0)
     all_the_tuples = re.findall(r"<input\stype=\'hidden\'\sname=\'(\S*?)\'\svalue=\'(\S*?)\'", temporary_filtered)
     time.sleep(30)
     herewego = None
     herewego = self.req.load('http://filesmonster.com/ajax.php', None, all_the_tuples)
     ticket_number = re.search(r"\"text\":\"(.*?)\"\,\"error\"", herewego).group(1)
     herewego = None
     herewego = self.req.load('http://filesmonster.com/ajax.php', None, {'act': 'getdl', 'data': ticket_number})
     ticket_number = None
     ticket_number = re.search(r"\"url\":\"(.*?)\"", herewego).group(1)
     the_download_page = re.sub(r"\\/", r"/", ticket_number)
     ticket_number = urllib.quote(the_download_page.encode('utf8')) 
     self.htmlwithlink = re.sub("http%3A", "http:", ticket_number) 
     self.filerequest = re.search(r"\"file_request\":\"(.*?)\"", herewego).group(1)

    def proceed(self, url, location):

        self.req.download(url, location, None, {"X-File-Request": self.filerequest})
