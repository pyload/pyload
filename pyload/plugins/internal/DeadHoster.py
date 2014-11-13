# -*- coding: utf-8 -*-

from pyload.plugins.base.Hoster import Hoster as _Hoster


def create_getInfo(plugin):

    def getInfo(urls):
        yield map(lambda url: ('#N/A: ' + url, 0, 1, url), urls)

    return getInfo


class DeadHoster(_Hoster):
    __name__    = "DeadHoster"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'^unmatchable$'

    __description__ = """Hoster is no longer available"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")
