# -*- coding: utf-8 -*-

from urllib import unquote
from urlparse import urlparse

from pyload.plugin.Hoster import Hoster as _Hoster
from pyload.plugin.internal.SimpleHoster import create_getInfo


class DeadHoster(_Hoster):
    __name__    = "DeadHoster"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'^unmatchable$'

    __description__ = """Hoster is no longer available"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    @classmethod
    def getInfo(cls, url="", html=""):
        return {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 1, 'url': url}


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")


getInfo = create_getInfo(DeadHoster)
