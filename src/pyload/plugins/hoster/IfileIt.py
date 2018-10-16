# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class IfileIt(DeadHoster):
    __name__ = "IfileIt"
    __type__ = "hoster"
    __version__ = "0.34"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"^unmatchable$"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Ifile.it hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
