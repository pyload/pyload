# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class FilerioCom(XFSHoster):
    __name    = "FilerioCom"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}'

    __description = """FileRio.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "filerio.in"

    URL_REPLACEMENTS = [(r'filekeen\.com', "filerio.in")]

    OFFLINE_PATTERN = r'>&quot;File Not Found|File has been removed'


getInfo = create_getInfo(FilerioCom)
