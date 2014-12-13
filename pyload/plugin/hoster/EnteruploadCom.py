# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class EnteruploadCom(DeadHoster):
    __name    = "EnteruploadCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?enterupload\.com/\w+'

    __description = """EnterUpload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(EnteruploadCom)
