# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class FilerioCom(XFSPHoster):
    __name__    = "FilerioCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}'

    __description__ = """FileRio.in hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "filerio.in"

    OFFLINE_PATTERN = r'>&quot;File Not Found|File has been removed'
    FILE_URL_REPLACEMENTS = [(r'http://.*?/', 'http://filerio.in/')]


getInfo = create_getInfo(FilerioCom)
