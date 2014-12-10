# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ZShareNet(DeadHoster):
    __name    = "ZShareNet"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'https?://(?:ww[2w]\.)?zshares?\.net/.+'

    __description = """ZShare.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("espes", None),
                       ("Cptn Sandwich", None)]


getInfo = create_getInfo(ZShareNet)
