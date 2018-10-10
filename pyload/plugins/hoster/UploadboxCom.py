# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster


class UploadboxCom(DeadHoster):
    __name__ = "Uploadbox"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?uploadbox\.com/files/.+'
    __config__ = []  # @TODO: Remove in 0.6.x

    __description__ = """UploadBox.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
