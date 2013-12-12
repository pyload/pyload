# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class Share76Com(DeadHoster):
    __name__ = "Share76Com"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?share76.com/\w{12}"
    __version__ = "0.04"
    __description__ = """share76.com hoster plugin"""
    __author_name__ = ("me")


getInfo = create_getInfo(Share76Com)
