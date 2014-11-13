# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadhereCom(DeadHoster):
    __name__    = "UploadhereCom"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'http://(?:www\.)?uploadhere\.com/\w{10}'

    __description__ = """Uploadhere.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(UploadhereCom)
