# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from os import makedirs
from os.path import exists
from urllib2 import build_opener

from MultipartPostHandler import MultipartPostHandler

from module.plugins.Container import Container
from module.utils import fs_encode, save_join


class CCF(Container):
    __name__    = "CCF"
    __type__    = "container"
    __version__ = "0.22"

    __pattern__ = r'.+\.ccf$'

    __description__ = """CCF container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Willnix", "Willnix@pyload.org")]


    def decrypt(self, pyfile):
        file   = fs_encode(pyfile.url.strip())
        opener = build_opener(MultipartPostHandler)

        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php',
                                      {'src'     : "ccf",
                                       'filename': "test.ccf",
                                       'upload'  : open(file, "rb")}).read()

        download_folder = self.config['general']['download_folder']
        tempdlc_name    = save_join(download_folder, "tmp_%s.dlc" % pyfile.name)

        with open(tempdlc_name, "w") as tempdlc:
            tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.S).group(1))

        self.urls = [tempdlc_name]
