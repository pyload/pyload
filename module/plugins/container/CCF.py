# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import urllib2

import MultipartPostHandler

from module.plugins.internal.Container import Container
from module.plugins.internal.utils import encode, fs_join


class CCF(Container):
    __name__    = "CCF"
    __type__    = "container"
    __version__ = "0.27"
    __status__  = "testing"

    __pattern__ = r'.+\.ccf$'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """CCF container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Willnix", "Willnix@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def decrypt(self, pyfile):
        fs_filename = encode(pyfile.url.strip())
        opener      = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)

        dlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php',
                                  {'src'     : "ccf",
                                   'filename': "test.ccf",
                                   'upload'  : open(fs_filename, "rb")}).read()

        dl_folder = self.pyload.config.get("general", "download_folder")
        dlc_file  = fs_join(dl_folder, "tmp_%s.dlc" % pyfile.name)

        try:
            dlc = re.search(r'<dlc>(.+)</dlc>', dlc_content, re.S).group(1).decode('base64')

        except AttributeError:
            self.fail(_("Container is corrupted"))

        with open(dlc_file, "w") as tempdlc:
            tempdlc.write(dlc)

        self.links = [dlc_file]
