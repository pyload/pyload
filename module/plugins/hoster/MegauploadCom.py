# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegauploadCom(DeadHoster):
    __name__    = "MegauploadCom"
    __type__    = "hoster"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?megaupload\.com/\?.*&?(d|v)=\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Megaupload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org")]


getInfo = create_getInfo(MegauploadCom)
