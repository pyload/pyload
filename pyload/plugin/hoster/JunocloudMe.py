# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class JunocloudMe(XFSHoster):
    __name    = "JunocloudMe"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:\w+\.)?junocloud\.me/\w{12}'

    __description = """Junocloud.me hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    URL_REPLACEMENTS = [(r'//(www\.)?junocloud', "//dl3.junocloud")]

    OFFLINE_PATTERN      = r'>No such file with this filename<'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'
