# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ZShareNet(DeadHoster):
    __name__    = "ZShareNet"
    __type__    = "hoster"
    __version__ = "0.22"
    __status__  = "testing"

    __pattern__ = r'https?://(?:ww[2w]\.)?zshares?\.net/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """ZShare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("espes", None),
                       ("Cptn Sandwich", None)]


getInfo = create_getInfo(ZShareNet)
