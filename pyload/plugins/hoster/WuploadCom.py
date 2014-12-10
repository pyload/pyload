# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WuploadCom(DeadHoster):
    __name    = "WuploadCom"
    __type    = "hoster"
    __version = "0.23"

    __pattern = r'http://(?:www\.)?wupload\..*?/file/((\w+/)?\d+)(/.*)?'

    __description = """Wupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de"),
                       ("Paul King", None)]


getInfo = create_getInfo(WuploadCom)
