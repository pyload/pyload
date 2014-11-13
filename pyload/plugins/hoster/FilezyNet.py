# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FilezyNet(DeadHoster):
    __name__    = "FilezyNet"
    __type__    = "hoster"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?filezy\.net/\w{12}'

    __description__ = """Filezy.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []


getInfo = create_getInfo(FilezyNet)
