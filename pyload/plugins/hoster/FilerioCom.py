# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class FilerioCom(XFSHoster):
    __name__    = "FilerioCom"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}'

    __description__ = """FileRio.in hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "filerio.in"

    OFFLINE_PATTERN = r'>&quot;File Not Found|File has been removed'
    URL_REPLACEMENTS = [(r'/(?:embed-)?(\w{12}).*', r'/\1'), (r'filekeen\.com', "filerio.in")]


getInfo = create_getInfo(FilerioCom)
