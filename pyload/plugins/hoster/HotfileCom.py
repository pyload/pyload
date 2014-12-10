# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class HotfileCom(DeadHoster):
    __name    = "HotfileCom"
    __type    = "hoster"
    __version = "0.37"

    __pattern = r'https?://(?:www\.)?hotfile\.com/dl/\d+/\w+'

    __description = """Hotfile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("sitacuisses", "sitacuisses@yhoo.de"),
                       ("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("JoKoT3", "jokot3@gmail.com")]


getInfo = create_getInfo(HotfileCom)
