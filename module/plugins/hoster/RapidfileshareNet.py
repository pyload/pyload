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

    FILE_NAME_PATTERN = r'<p class="request_file">http://rapidfileshare.net/w{12}/(?P<N>.+?)</p>'
    FILE_SIZE_PATTERN = r'<p class="request_filesize">Size: (?P<S>[\d.]+) (?P<U>\w+)</p>'

    OFFLINE_PATTERN = r'>(No such file|Software error:<)'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'


getInfo = create_getInfo(JunocloudMe)
