# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class BillionuploadsCom(XFileSharingPro):
    __name__ = "BillionuploadsCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?billionuploads\.com/\w{12}'

    __description__ = """Billionuploads.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    HOSTER_NAME = "billionuploads.com"

    FILE_NAME_PATTERN = r'<td class="dofir" title="(?P<N>.+?)"'
    FILE_SIZE_PATTERN = r'<td class="dofir">(?P<S>[\d.]+) (?P<U>\w+)'


getInfo = create_getInfo(BillionuploadsCom)
