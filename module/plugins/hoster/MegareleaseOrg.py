# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegareleaseOrg(DeadHoster):
    __name__    = "MegareleaseOrg"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?megarelease\.org/\w{12}'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Megarelease.org hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("derek3x", "derek3x@vmail.me"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(MegareleaseOrg)
