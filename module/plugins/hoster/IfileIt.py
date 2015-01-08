# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IfileIt(DeadHoster):
    __name__    = "IfileIt"
    __type__    = "hoster"
    __version__ = "0.29"

    __pattern__ = r'^unmatchable$'

    __description__ = """Ifile.it"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(IfileIt)
