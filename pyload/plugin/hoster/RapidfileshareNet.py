# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class RapidfileshareNet(XFSHoster):
    __name    = "RapidfileshareNet"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?rapidfileshare\.net/\w{12}'

    __description = """Rapidfileshare.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'>http://www.rapidfileshare.net/\w+?</font> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</font>'

    OFFLINE_PATTERN      = r'>No such file with this filename'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'
