# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class MegauploadCom(DeadHoster):
    __name    = "MegauploadCom"
    __type    = "hoster"
    __version = "0.31"

    __pattern = r'http://(?:www\.)?megaupload\.com/\?.*&?(d|v)=\w+'

    __description = """Megaupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org")]


getInfo = create_getInfo(MegauploadCom)
