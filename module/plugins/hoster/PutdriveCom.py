# -*- coding: utf-8 -*-

from module.plugins.hosters.ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name__    = "PutdriveCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)putdrive\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'

    __description__ = """Multihosters.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
