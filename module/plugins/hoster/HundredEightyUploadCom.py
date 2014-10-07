# -*- coding: utf-8 -*-
#
# Test links:
# http://180upload.com/js9qdm6kjnrs

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class HundredEightyUploadCom(XFileSharingPro):
    __name__ = "HundredEightyUploadCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?180upload\.com/\w{12}'

    __description__ = """180upload.com hoster plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_NAME = "180upload.com"

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.+)</td></tr>-->'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.]+) (?P<U>[A-Z]+)\s*<small>'


getInfo = create_getInfo(HundredEightyUploadCom)
