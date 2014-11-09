# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class HotfileCom(DeadHoster):
    __name__    = "HotfileCom"
    __type__    = "hoster"
    __version__ = "0.37"

    __pattern__ = r'https?://(?:www\.)?hotfile\.com/dl/\d+/\w+'

    __description__ = """Hotfile.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sitacuisses", "sitacuisses@yhoo.de"),
                       ("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("JoKoT3", "jokot3@gmail.com")]


getInfo = create_getInfo(HotfileCom)
