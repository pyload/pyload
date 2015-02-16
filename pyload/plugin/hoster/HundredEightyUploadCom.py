# -*- coding: utf-8 -*-
#
# Test links:
# http://180upload.com/js9qdm6kjnrs

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class HundredEightyUploadCom(XFSHoster):
    __name__    = "HundredEightyUploadCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?180upload\.com/\w{12}'

    __description__ = """180upload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "180upload.com"

    NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.+)</td></tr>-->'
    SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.,]+) (?P<U>[\w^_]+)\s*<small>'


getInfo = create_getInfo(HundredEightyUploadCom)
