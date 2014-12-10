# -*- coding: utf-8 -*-

from urllib import unquote
from urlparse import urlparse

from pyload.plugins.Hoster import Hoster as _Hoster
from pyload.plugins.internal.SimpleHoster import create_getInfo


class DeadHoster(_Hoster):
    __name    = "DeadHoster"
    __type    = "hoster"
    __version = "0.14"

    __pattern = r'^unmatchable$'

    __description = """Hoster is no longer available"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    @classmethod
    def getInfo(cls, url="", html=""):
        return {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 1, 'url': url}


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")


getInfo = create_getInfo(DeadHoster)
