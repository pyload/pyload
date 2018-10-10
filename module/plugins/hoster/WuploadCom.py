# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class WuploadCom(DeadHoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __version__ = "0.28"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?wupload\..+?/file/((\w+/)?\d+)(/.*)?'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Wupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("Paul King", None)]
