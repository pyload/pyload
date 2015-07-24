# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class EnteruploadCom(DeadHoster):
    __name__    = "EnteruploadCom"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?enterupload\.com/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """EnterUpload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(EnteruploadCom)
