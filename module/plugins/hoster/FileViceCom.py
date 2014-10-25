# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class FileViceCom(XFSPHoster):
    __name__ = "FileViceCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(www\.)?filevice\.com/[a-z0-9]{12}(/\S+)?'

    __description__ = """FileVice.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]

    HOSTER_NAME = "filevice.com"

getInfo = create_getInfo(FileViceCom)
