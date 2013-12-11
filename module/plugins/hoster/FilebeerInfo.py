# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo, create_getInfo


class FilebeerInfo(DeadHoster):
    __name__ = "FilebeerInfo"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+)"
    __version__ = "0.03"
    __description__ = """Filebeer.info plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")


getInfo = create_getInfo(FilebeerInfo)
