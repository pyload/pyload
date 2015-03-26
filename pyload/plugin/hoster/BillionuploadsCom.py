# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class BillionuploadsCom(XFSHoster):
    __name__    = "BillionuploadsCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?billionuploads\.com/\w{12}'

    __description__ = """Billionuploads.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<td class="dofir" title="(?P<N>.+?)"'
    SIZE_PATTERN = r'<td class="dofir">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
