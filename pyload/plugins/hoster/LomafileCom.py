# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class LomafileCom(XFSHoster):
    __name__    = "LomafileCom"
    __type__    = "hoster"
    __version__ = "0.51"

    __pattern__ = r'http://lomafile\.com/\w{12}'

    __description__ = """Lomafile.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "lomafile.com"

    NAME_PATTERN = r'<a href="http://lomafile\.com/w{12}/(?P<N>.+?)">'
    SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>(No such file|Software error:<)'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'

    CAPTCHA_PATTERN = r'(http://lomafile\.com/captchas/[^"\']+)'


getInfo = create_getInfo(LomafileCom)
