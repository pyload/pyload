# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class RapidfileshareNet(XFSPHoster):
    __name__ = "RapidfileshareNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?rapidfileshare\.net/\w{12}'

    __description__ = """Rapidfileshare.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = ("guidobelix", "guidobelix@hotmail.it")


    HOSTER_NAME = "rapidfileshare.net"

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>.+?)">'
    FILE_SIZE_PATTERN = r'>http://www.rapidfileshare.net/\w+?</font> \((?P<S>[\d\.\,]+) (?P<U>\w+)\)</font>'

    OFFLINE_PATTERN = r'>No such file with this filename<'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'


    def handlePremium(self):
        self.fail("Premium download not implemented")


getInfo = create_getInfo(RapidfileshareNet)
