# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SharingmatrixCom(DeadHoster):
    __name    = "SharingmatrixCom"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sharingmatrix\.com/file/\w+'

    __description = """Sharingmatrix.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de"),
                       ("paulking", None)]


getInfo = create_getInfo(SharingmatrixCom)
