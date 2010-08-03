#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib2

from module.plugins.Container import Container
from module.network.MultipartPostHandler import MultipartPostHandler

class CCF(Container):
    __name__ = "CCF"
    __version__ = "0.2"
    __pattern__ = r"(?!http://).*\.ccf"
    __description__ = """CCF Container Convert Plugin"""
    __author_name__ = ("Willnix")
    __author_mail__ = ("Willnix@pyload.org")

    def decrypt(self, pyfile):
        self.loadToDisk()
    
        infile = pyfile.url.replace("\n", "")

        opener = urllib2.build_opener(MultipartPostHandler)
        params = {"src": "ccf",
            "filename": "test.ccf",
            "upload": open(infile, "rb")}
        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', params).read()

        download_folder = self.config['general']['download_folder']
        location = download_folder #join(download_folder, self.pyfile.package().folder.decode(sys.getfilesystemencoding()))
        if not exists(location): 
            makedirs(location)
            
        tempdlc_name = "tmp_%s.dlc" % join(location, pyfile.name)
        tempdlc = open(tempdlc_name, "w")
        tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
        tempdlc.close()

        self.packages.append((tempdlc_name, [tempdlc_name], tempdlc_name))

