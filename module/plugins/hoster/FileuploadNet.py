# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileuploadNet(SimpleHoster):
    __name__    = "FileuploadNet"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(en\.)?file-upload\.net/download-\d+/.+'

    __description__ = """File-upload.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'<title>File-Upload.net - (?P<N>.+?)<'
    SIZE_PATTERN    = r'</label><span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Datei existiert nicht'

    LINK_FREE_PATTERN = r"<a href='(.+?)' title='download' onclick"


    def setup(self):
        self.multiDL    = True
        self.chunk_limit = 1


getInfo = create_getInfo(FileuploadNet)
