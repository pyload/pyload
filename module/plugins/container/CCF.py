# -*- coding: utf-8 -*-

import re

from os import makedirs
from os.path import exists
from urllib2 import build_opener

from module.lib.MultipartPostHandler import MultipartPostHandler

from module.plugins.Container import Container
from module.utils import safe_join


class CCF(Container):
    __name__ = "CCF"
    __version__ = "0.2"

    __pattern__ = r'.+\.ccf'

    __description__ = """CCF container decrypter plugin"""
    __author_name__ = "Willnix"
    __author_mail__ = "Willnix@pyload.org"


    def decrypt(self, pyfile):

        infile = pyfile.url.replace("\n", "")

        opener = build_opener(MultipartPostHandler)
        params = {"src": "ccf",
            "filename": "test.ccf",
            "upload": open(infile, "rb")}
        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', params).read()

        download_folder = self.config['general']['download_folder']

        tempdlc_name = safe_join(download_folder, "tmp_%s.dlc" % pyfile.name)
        tempdlc = open(tempdlc_name, "w")
        tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
        tempdlc.close()

        self.urls = [tempdlc_name]
