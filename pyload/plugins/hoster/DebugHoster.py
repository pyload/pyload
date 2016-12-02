# -*- coding: utf-8 -*-

from time import sleep
from random import randint

from pyload.Api import LinkStatus, DownloadStatus as DS
from pyload.plugins.Hoster import Hoster


class DebugHoster(Hoster):
    """ Generates link used by debug hoster to test the decrypt mechanism """

    __version__ = 0.1
    __pattern__ = r"^debug_hoster=\d*$"

    @classmethod
    def getInfo(cls, urls):
        for url in urls:
            yield LinkStatus(url, url + " - checked", randint(1024, 2048), DS.Online)
            sleep(1)

    def process(self, pyfile):
        pass
