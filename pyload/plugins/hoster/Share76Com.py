# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class Share76Com(DeadHoster):
    __name__ = "Share76Com"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?share76.com/\w{12}'

    __description__ = """Share76.com hoster plugin"""
    __author_name__ = "me"
    __author_mail__ = None


getInfo = create_getInfo(Share76Com)
