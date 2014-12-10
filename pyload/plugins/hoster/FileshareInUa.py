# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FileshareInUa(DeadHoster):
    __name    = "FileshareInUa"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)?fileshare\.in\.ua/\w{7}'

    __description = """Fileshare.in.ua hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("fwannmacher", "felipe@warhammerproject.com")]


getInfo = create_getInfo(FileshareInUa)
