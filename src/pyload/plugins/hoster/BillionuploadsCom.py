# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class BillionuploadsCom(DeadHoster):
    __name__ = "BillionuploadsCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?billionuploads\.com/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Billionuploads.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
