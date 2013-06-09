# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class BillionuploadsCom(XFileSharingPro):
    __name__ = "BillionuploadsCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?billionuploads.com/\w{12}"
    __version__ = "0.01"
    __description__ = """billionuploads.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<b>Filename:</b>(?P<N>.*?)<br>'
    FILE_SIZE_PATTERN = r'<b>Size:</b>(?P<S>.*?)<br>'
    HOSTER_NAME = "billionuploads.com"

getInfo = create_getInfo(BillionuploadsCom)
