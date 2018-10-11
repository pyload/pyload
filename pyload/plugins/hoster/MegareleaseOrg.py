# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster


class MegareleaseOrg(DeadHoster):
    __name__ = "MegareleaseOrg"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?megarelease\.org/\w{12}'
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Megarelease.org hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("derek3x", "derek3x@vmail.me"),
                   ("stickell", "l.stickell@yahoo.it")]
