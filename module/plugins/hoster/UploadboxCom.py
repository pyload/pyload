# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadboxCom(DeadHoster):
    __name__    = "Uploadbox"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?uploadbox\.com/files/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """UploadBox.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(UploadboxCom)
