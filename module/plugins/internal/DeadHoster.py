# -*- coding: utf-8 -*-

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.SimpleHoster import create_getInfo


class DeadHoster(Hoster):
    __name__    = "DeadHoster"
    __type__    = "hoster"
    __version__ = "0.16"

    __pattern__ = r'^unmatchable$'

    __description__ = """Hoster is no longer available"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    @classmethod
    def apiInfo(cls, *args, **kwargs):
        api = super(DeadHoster, cls).apiInfo(*args, **kwargs)
        api['status'] = 1
        return api


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")


getInfo = create_getInfo(DeadHoster)
