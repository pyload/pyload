#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib2 import build_opener

from module.plugins.Crypter import Crypter
from module.lib.MultipartPostHandler import MultipartPostHandler

from os import makedirs
from os.path import exists, join

class CCF(Crypter):
    __name__ = "CCF"
    __version__ = "0.2"
    __pattern__ = r"(?!http://).*\.ccf$"
    __description__ = """CCF Container Convert Plugin"""
    __author_name__ = ("Willnix")
    __author_mail__ = ("Willnix@pyload.org")

    def decrypt(self, pyfile):
    
        infile = pyfile.url.replace("\n", "")

        opener = build_opener(MultipartPostHandler)
        params = {"src": "ccf",
            "filename": "test.ccf",
            "upload": open(infile, "rb")}
        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', params).read()

        download_folder = self.config['general']['download_folder']
        location = download_folder #join(download_folder, self.pyfile.package().folder.decode(sys.getfilesystemencoding()))
        if not exists(location): 
            makedirs(location)
            
        tempdlc_name = join(location, "tmp_%s.dlc" % pyfile.name)
        tempdlc = open(tempdlc_name, "w")
        tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
        tempdlc.close()

        self.packages.append((tempdlc_name, [tempdlc_name], tempdlc_name))

