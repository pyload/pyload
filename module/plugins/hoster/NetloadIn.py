# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class NetloadIn(DeadHoster):
    __name__ = "NetloadIn"
    __type__ = "hoster"
    __version__ = "0.55"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?netload\.(in|me)/(?P<PATH>datei|index\.php\?id=10&file_id=)(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Netload.in hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org"),
                   ("RaNaN", "ranan@pyload.org"),
                   ("Gregy", "gregy@gregy.cz")]
