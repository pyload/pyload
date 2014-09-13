# -*- coding: utf-8 -*-
#
# Test links:
# http://fileom.com/gycaytyzdw3g/random.bin.html

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class FileomCom(XFileSharingPro):
    __name__ = "FileomCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?fileom\.com/\w+'

    __description__ = """Fileom.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "fileom.com"

    FILE_URL_REPLACEMENTS = [(r'/$', "")]
    SH_COOKIES = [(".fileom.com", "lang", "english")]

    FILE_NAME_PATTERN = r'Filename: <span>(?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'File Size: <span class="size">(?P<S>[\d\.]+) (?P<U>\w+)'

    ERROR_PATTERN = r'class=["\']err["\'][^>]*>(.*?)(?:\'|</)'

    LINK_PATTERN = r"var url2 = '(.+?)';"


    def setup(self):
        self.resumeDownload = self.premium
        self.multiDL = True
        self.chunkLimit = 1


getInfo = create_getInfo(FileomCom)
