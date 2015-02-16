# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class MegareleaseOrg(DeadHoster):
    __name    = "MegareleaseOrg"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)?megarelease\.org/\w{12}'

    __description = """Megarelease.org hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("derek3x", "derek3x@vmail.me"),
                       ("stickell", "l.stickell@yahoo.it")]
