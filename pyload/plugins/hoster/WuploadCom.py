#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WuploadCom(DeadHoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?wupload\..*?/file/(([a-z][0-9]+/)?[0-9]+)(/.*)?"
    __version__ = "0.23"
    __description__ = """Wupload com"""
    __author_name__ = ("jeix", "paulking")
    __author_mail__ = ("jeix@hasnomail.de", "")


getInfo = create_getInfo(WuploadCom)
