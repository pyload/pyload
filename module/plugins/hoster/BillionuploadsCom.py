# -*- coding: utf-8 -*-

from module.plugins.hoster.XFSPHoster import XFSPHoster, create_getInfo


class BillionuploadsCom(XFSPHoster):
    __name__ = "BillionuploadsCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?billionuploads\.com/\w{12}'

    __description__ = """Billionuploads.com hoster plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "billionuploads.com"

    FILE_NAME_PATTERN = r'<td class="dofir" title="(?P<N>.+?)"'
    FILE_SIZE_PATTERN = r'<td class="dofir">(?P<S>[\d.]+) (?P<U>\w+)'


getInfo = create_getInfo(BillionuploadsCom)
