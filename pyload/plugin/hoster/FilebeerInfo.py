# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class FilebeerInfo(DeadHoster):
    __name    = "FilebeerInfo"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+)'

    __description = """Filebeer.info plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
