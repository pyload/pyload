# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WuploadCom(DeadHoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __version__ = "0.23"

    __pattern__ = r'http://(?:www\.)?wupload\..*?/file/(([a-z][0-9]+/)?[0-9]+)(/.*)?'

    __description__ = """Wupload.com hoster plugin"""
    __author_name__ = ("jeix", "Paul King")
    __author_mail__ = ("jeix@hasnomail.de", "")


getInfo = create_getInfo(WuploadCom)
