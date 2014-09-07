# -*- coding: utf-8 -*-

import re

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class FileParadoxIn(XFileSharingPro):
    __name__ = "FileParadoxIn"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?fileparadox\.in/\w+'

    __description__ = """FileParadox.in hoster plugin"""
    __author_name__ = "RazorWing"
    __author_mail__ = "muppetuk1@hotmail.com"

    HOSTER_NAME = "fileparadox.in"

    FILE_SIZE_PATTERN = r'</font>\s*\(\s*(?P<S>[^)]+)\s*\)</font>'
    LINK_PATTERN = r'(http://([^/]*?fileparadox.in|\d+\.\d+\.\d+\.\d+)(:\d+/d/|/files/\w+/\w+/)[^"\'<]+)'


getInfo = create_getInfo(FileParadoxIn)
