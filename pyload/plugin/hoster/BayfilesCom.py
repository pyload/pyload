# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class BayfilesCom(DeadHoster):
    __name    = "BayfilesCom"
    __type    = "hoster"
    __version = "0.09"

    __pattern = r'https?://(?:www\.)?bayfiles\.(com|net)/file/(?P<ID>\w+/\w+/[^/]+)'

    __description = """Bayfiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]
