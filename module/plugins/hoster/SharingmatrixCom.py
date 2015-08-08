# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SharingmatrixCom(DeadHoster):
    __name__    = "SharingmatrixCom"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?sharingmatrix\.com/file/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Sharingmatrix.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("paulking", None)]


getInfo = create_getInfo(SharingmatrixCom)
