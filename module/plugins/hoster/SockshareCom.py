# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class SockshareCom(DeadHoster):
    __name__ = "SockshareCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?sockshare\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Sockshare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("Walter Purcaro", "vuolter@gmail.com")]
