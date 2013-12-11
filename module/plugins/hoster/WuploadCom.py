#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class WuploadCom(DeadHoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:\w+\.)*?wupload\.((?P<NP>eu/rr/)|com/file/)(?P<ID>(?(NP)[^/]|\d)+)"
    __version__ = "0.23"
    __description__ = """Wupload com"""
    __author_name__ = ("jeix", "paulking")
    __author_mail__ = ("jeix@hasnomail.de", "")


getInfo = create_getInfo(WuploadCom)
