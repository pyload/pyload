# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster


class ShragleCom(DeadHoster):
    __name__    = "ShragleCom"
    __type__    = "hoster"
    __version__ = "0.26"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?(cloudnator|shragle)\.com/files/(?P<ID>.+?)/'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Cloudnator.com (Shragle.com) hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz")]
