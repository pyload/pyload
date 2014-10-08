# -*- coding: utf-8 -*-
#
# Test links:
# http://fileom.com/gycaytyzdw3g/random.bin.html

from module.plugins.hoster.XFSPHoster import XFSPHoster, create_getInfo


class FileomCom(XFSPHoster):
    __name__ = "FileomCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?fileom\.com/\w{12}'

    __description__ = """Fileom.com hoster plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "fileom.com"

    FILE_URL_REPLACEMENTS = [(r'/$', "")]

    FILE_NAME_PATTERN = r'Filename: <span>(?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'File Size: <span class="size">(?P<S>[\d\.]+) (?P<U>\w+)'

    ERROR_PATTERN = r'class=["\']err["\'][^>]*>(.*?)(?:\'|</)'

    LINK_PATTERN = r"var url2 = '(.+?)';"


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = self.premium


getInfo = create_getInfo(FileomCom)
