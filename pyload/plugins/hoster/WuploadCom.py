# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WuploadCom(DeadHoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __version__ = "0.23"

    __pattern__ = r'http://(?:www\.)?wupload\..*?/file/(([a-z][0-9]+/)?[0-9]+)(/.*)?'

    __description__ = """Wupload.com hoster plugin"""
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("Paul King", None)]


getInfo = create_getInfo(WuploadCom)
