# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class FileParadoxIn(XFSHoster):
    __name    = "FileParadoxIn"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'https?://(?:www\.)?fileparadox\.in/\w{12}'

    __description = """FileParadox.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("RazorWing", "muppetuk1@hotmail.com")]


    HOSTER_DOMAIN = "fileparadox.in"

    SIZE_PATTERN = r'</font>\s*\(\s*(?P<S>[^)]+)\s*\)</font>'


getInfo = create_getInfo(FileParadoxIn)
