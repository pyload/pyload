# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class BillionuploadsCom(DeadHoster):
    __name    = "BillionuploadsCom"
    __type    = "hoster"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?billionuploads\.com/\w{12}'

    __description = """Billionuploads.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
