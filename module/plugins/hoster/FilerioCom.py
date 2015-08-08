# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class FilerioCom(XFSHoster):
    __name__    = "FilerioCom"
    __type__    = "hoster"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}'

    __description__ = """FileRio.in hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    URL_REPLACEMENTS = [(r'filekeen\.com', "filerio.in")]

    OFFLINE_PATTERN = r'>&quot;File Not Found|File has been removed'


getInfo = create_getInfo(FilerioCom)
