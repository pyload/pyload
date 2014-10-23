# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class SafesharingEu(XFSAccount):
    __name__ = "SafesharingEu"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Safesharing.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "safesharing.eu"

    VALID_UNTIL_PATTERN = r'> Premium.[Aa]ccount expire:(.+?)</div>'
    TRAFFIC_LEFT_PATTERN = r'> Traffic available today:\s*?(?P<S>[\d.,]+)\s*?(?:(?P<U>[\w^_]+)\s*)?</div>'
