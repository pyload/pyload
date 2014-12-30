# -*- coding: utf-8 -*-
#
# Test links:
# http://fileom.com/gycaytyzdw3g/random.bin.html

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class FileomCom(XFSHoster):
    __name__    = "FileomCom"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?fileom\.com/\w{12}'

    __description__ = """Fileom.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "fileom.com"

    NAME_PATTERN = r'Filename: <span>(?P<N>.+?)<'
    SIZE_PATTERN = r'File Size: <span class="size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    LINK_PATTERN = r'var url2 = \'(.+?)\';'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = self.premium


getInfo = create_getInfo(FileomCom)
