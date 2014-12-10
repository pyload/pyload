# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FilesonicCom(DeadHoster):
    __name    = "FilesonicCom"
    __type    = "hoster"
    __version = "0.35"

    __pattern = r'http://(?:www\.)?filesonic\.com/file/\w+'

    __description = """Filesonic.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de"),
                       ("paulking", None)]


getInfo = create_getInfo(FilesonicCom)
