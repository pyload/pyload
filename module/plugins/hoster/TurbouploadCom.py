# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class TurbouploadCom(DeadHoster):
    __name__ = "TurbouploadCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?turboupload.com/(\w+).*'

    __description__ = """Turboupload.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


getInfo = create_getInfo(TurbouploadCom)
