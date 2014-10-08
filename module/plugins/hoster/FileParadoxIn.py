# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class FileParadoxIn(XFSPHoster):
    __name__ = "FileParadoxIn"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?fileparadox\.in/\w{12}'

    __description__ = """FileParadox.in hoster plugin"""
    __authors__ = [("RazorWing", "muppetuk1@hotmail.com")]


    HOSTER_NAME = "fileparadox.in"

    FILE_SIZE_PATTERN = r'</font>\s*\(\s*(?P<S>[^)]+)\s*\)</font>'
    LINK_PATTERN = r'(http://([^/]*?fileparadox.in|\d+\.\d+\.\d+\.\d+)(:\d+/d/|/files/\w+/\w+/)[^"\'<]+)'


getInfo = create_getInfo(FileParadoxIn)
