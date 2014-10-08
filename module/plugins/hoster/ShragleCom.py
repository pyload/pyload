# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ShragleCom(DeadHoster):
    __name__ = "ShragleCom"
    __type__ = "hoster"
    __version__ = "0.22"

    __pattern__ = r'http://(?:www\.)?(cloudnator|shragle).com/files/(?P<ID>.*?)/'

    __description__ = """Cloudnator.com (Shragle.com) hoster plugin"""
    __authors__ = [("RaNaN", "RaNaN@pyload.org"),
                   ("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(ShragleCom)
