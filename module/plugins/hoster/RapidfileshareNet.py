# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class RapidfileshareNet(XFSHoster):
    __name__    = "RapidfileshareNet"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?rapidfileshare\.net/\w{12}'

    __description__ = """Rapidfileshare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "rapidfileshare.net"

    NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'>http://www.rapidfileshare.net/\w+?</font> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</font>'

    OFFLINE_PATTERN      = r'>No such file with this filename'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'


getInfo = create_getInfo(RapidfileshareNet)
