# -*- coding: utf-8 -*-

from urlparse import urlparse

from module.plugins.internal.SimpleHoster import create_getInfo
from module.plugins.Hoster import Hoster as _Hoster


class DeadHoster(_Hoster):
    __name__    = "DeadHoster"
    __type__    = "hoster"
    __version__ = "0.13"

    __pattern__ = r'^unmatchable$'

    __description__ = """ Hoster is no longer available """
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    @classmethod
    def getInfo(cls, url="", html=""):
        return {'name': urlparse(url).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 1, 'url': url or ""}


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")


getInfo = create_getInfo(DeadHoster)
