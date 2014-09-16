# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class LomafileCom(XFileSharingPro):
    __name__ = "LomafileCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://lomafile\.com/.+/[\w\.]+'

    __description__ = """ Lomafile.com hoster plugin """
    __author_name__ = "nath_schwarz", "guidobelix"
    __author_mail__ = "nathan.notwhite@gmail.com", "guidobelix@hotmail.it"

    HOSTER_NAME = "lomafile.com"

    FILE_NAME_PATTERN = r'<a href="http://lomafile.com/w{12}/(?P<N>[\w\.]+?)">'
#   Old definition of FILE_NAME_PATTERN replaced to deal with special characters
    FILE_SIZE_PATTERN = r'\((?P<S>\d+)\s(?P<U>\w+)\)'
    OFFLINE_PATTERN = r'No such file with this filename'

    CAPTCHA_URL_PATTERN = r'(http://lomafile\.com/captchas/[^"\']+)'


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium



getInfo = create_getInfo(LomafileCom)
