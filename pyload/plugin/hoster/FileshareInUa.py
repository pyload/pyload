# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class FileshareInUa(DeadHoster):
    __name    = "FileshareInUa"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)?fileshare\.in\.ua/\w{7}'
    __config  = []

    __description = """Fileshare.in.ua hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("fwannmacher", "felipe@warhammerproject.com")]
