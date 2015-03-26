# -*- coding: utf-8 -*-

from pyload.plugin.hoster.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name    = "MultihostersCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)multihosters\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'

    __description = """Multihosters.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("tjeh", "tjeh@gmx.net")]
