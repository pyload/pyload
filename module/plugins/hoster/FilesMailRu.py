#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class FilesMailRu(Hoster):
    __name__ = "FilesMailRu"
    __type__ = "hoster"
    __pattern__ = r"http://files\.mail\.ru/.*"
    __version__ = "0.1"
    __description__ = """Files.Mail.Ru One-Klick Hoster"""
    __author_name__ = ("oZiRiz")
    __author_mail__ = ("ich@oziriz.de")

    def process(self, pyfile):
        self.html = self.load(pyfile.url)
        self.url_pattern = '<a href="(.+?)" onclick="return Act\(this\, \'dlink\'\, event\)">(.+?)</a>'
        
        #marks the file as "offline" when the pattern was found on the html-page'''
        if re.search(r'<div class="errorMessage mb10">', self.html) is not None:
            self.offline()
        
        
        #the filename that will be showed in the list (e.g. test.part1.rar)'''
        pyfile.name = self.getFileName()
        
        #prepare and download'''
        self.prepare()
        self.download(self.getFileUrl())
        
        
        

    def prepare(self):
        '''You have to wait some seconds. Otherwise you will get a 40Byte HTML Page instead of the file you expected'''
        self.setWait(10)
        self.wait()
        return True
        
    def getFileUrl(self):
        '''gives you the URL to the file. Extracted from the Files.mail.ru HTML-page stored in self.html'''
        file_url = re.search(self.url_pattern, self.html).group(0).split('<a href="')[1].split('" onclick="return Act')[0]
        return file_url


    def getFileName(self):
        '''gives you the Name for each file. Also extracted from the HTML-Page'''
        file_name = re.search(self.url_pattern, self.html).group(0).split(', event)">')[1].split('</a>')[0]
        return file_name
