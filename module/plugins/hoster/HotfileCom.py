# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class HotfileCom(DeadHoster):
    __name__ = "HotfileCom"
    __type__ = "hoster"
    __version__ = "0.37"

    __pattern__ = r'https?://(?:www\.)?hotfile\.com/dl/\d+/\w+'

    __description__ = """Hotfile.com hoster plugin"""
    __author_name__ = ("sitacuisses", "spoob", "mkaay", "JoKoT3")
    __author_mail__ = ("sitacuisses@yhoo.de", "spoob@pyload.org", "mkaay@mkaay.de", "jokot3@gmail.com")


getInfo = create_getInfo(HotfileCom)
