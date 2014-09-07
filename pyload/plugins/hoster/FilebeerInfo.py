# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FilebeerInfo(DeadHoster):
    __name__ = "FilebeerInfo"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+).*'

    __description__ = """Filebeer.info plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


getInfo = create_getInfo(FilebeerInfo)
