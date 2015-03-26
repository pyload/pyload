# -*- coding: utf-8 -*-

from pyload.plugin.hoster.ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name    = "PutdriveCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)putdrive\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'

    __description = """Multihosters.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]
