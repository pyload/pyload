# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class WorldbytezCom(XFSAccount):
    __name__ = "WorldbytezCom"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Worldbytez.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "worldbytez.com"
    PLUGIN_URL = "https://worldbytez.com/"

    PREMIUM_PATTERN = r">Premium Is Enabled<"
    VALID_UNTIL_PATTERN = r">Expire (.+?)<"
    TRAFFIC_LEFT_PATTERN = r">Daily Traffic .*<p [\w'\"=-]+> (?P<U>[\w^_]+) <sup></sup> (?P<S>[\d.,]+)<"
