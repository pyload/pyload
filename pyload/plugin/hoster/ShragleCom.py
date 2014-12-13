# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class ShragleCom(DeadHoster):
    __name    = "ShragleCom"
    __type    = "hoster"
    __version = "0.22"

    __pattern = r'http://(?:www\.)?(cloudnator|shragle)\.com/files/(?P<ID>.*?)/'

    __description = """Cloudnator.com (Shragle.com) hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(ShragleCom)
