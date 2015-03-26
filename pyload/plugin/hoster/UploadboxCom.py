# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadboxCom(DeadHoster):
    __name__    = "Uploadbox"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?uploadbox\.com/files/.+'

    __description__ = """UploadBox.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
