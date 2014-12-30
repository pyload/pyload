# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class FileParadoxIn(XFSHoster):
    __name__    = "FileParadoxIn"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?fileparadox\.in/\w{12}'

    __description__ = """FileParadox.in hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RazorWing", "muppetuk1@hotmail.com")]


    HOSTER_DOMAIN = "fileparadox.in"


getInfo = create_getInfo(FileParadoxIn)
