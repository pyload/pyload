# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class PandaplaNet(DeadHoster):
    __name__    = "PandaplaNet"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?pandapla\.net/\w{12}'

    __description__ = """Pandapla.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


getInfo = create_getInfo(PandaplaNet)
