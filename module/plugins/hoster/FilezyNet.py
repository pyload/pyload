# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FilezyNet(DeadHoster):
    __name__    = "FilezyNet"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?filezy\.net/\w{12}'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Filezy.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []


getInfo = create_getInfo(FilezyNet)
