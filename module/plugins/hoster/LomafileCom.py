# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class LomafileCom(XFileSharingPro):
    __name__ = "LomafileCom"
    __type__ = "hoster"
    __version__ = "0.3"

    __pattern__ = r'http://lomafile\.com/\w{12}'

    __description__ = """Lomafile.com hoster plugin"""
    __authors__ = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                   ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "lomafile.com"

    FILE_NAME_PATTERN = r'<a href="http://lomafile\.com/w{12}/(?P<N>.+?)">'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>(?P<S>[\d.]+) (?P<U>\w+)'

    OFFLINE_PATTERN = r'>(No such file|Software error:<)'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'

    CAPTCHA_URL_PATTERN = r'(http://lomafile\.com/captchas/[^"\']+)'


getInfo = create_getInfo(LomafileCom)
