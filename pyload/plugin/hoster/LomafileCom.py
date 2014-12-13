# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class LomafileCom(XFSHoster):
    __name    = "LomafileCom"
    __type    = "hoster"
    __version = "0.51"

    __pattern = r'http://lomafile\.com/\w{12}'

    __description = """Lomafile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "lomafile.com"

    NAME_PATTERN = r'<a href="http://lomafile\.com/w{12}/(?P<N>.+?)">'
    SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>(No such file|Software error:<)'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'

    CAPTCHA_PATTERN = r'(http://lomafile\.com/captchas/[^"\']+)'


getInfo = create_getInfo(LomafileCom)
