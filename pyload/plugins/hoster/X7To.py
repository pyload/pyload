# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class X7To(DeadHoster):
    __name__ = "X7To"
    __type__ = "hoster"
    __version__ = "0.41"

    __pattern__ = r'http://(?:www\.)?x7.to/'

    __description__ = """X7.to hoster plugin"""
    __author_name__ = "ernieb"
    __author_mail__ = "ernieb"


getInfo = create_getInfo(X7To)
