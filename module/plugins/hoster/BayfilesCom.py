# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class BayfilesCom(DeadHoster):
    __name__    = "BayfilesCom"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?bayfiles\.(com|net)/file/(?P<ID>\w+/\w+/[^/]+)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Bayfiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(BayfilesCom)
