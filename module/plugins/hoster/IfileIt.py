# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IfileIt(DeadHoster):
    __name__    = "IfileIt"
    __type__    = "hoster"
    __version__ = "0.30"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Ifile.it hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(IfileIt)
