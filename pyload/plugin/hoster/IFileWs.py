# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class IFileWs(DeadHoster):
    __name    = "IFileWs"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?ifile\.ws/\w{12}'

    __description = """Ifile.ws hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]
