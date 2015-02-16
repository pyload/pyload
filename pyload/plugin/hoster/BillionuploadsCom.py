# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class BillionuploadsCom(XFSHoster):
    __name    = "BillionuploadsCom"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?billionuploads\.com/\w{12}'

    __description = """Billionuploads.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<td class="dofir" title="(?P<N>.+?)"'
    SIZE_PATTERN = r'<td class="dofir">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
