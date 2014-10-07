# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegareleaseOrg(DeadHoster):
    __name__ = "MegareleaseOrg"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?megarelease\.org/\w{12}'

    __description__ = """Megarelease.org hoster plugin"""
    __author_name__ = ("derek3x", "stickell")
    __author_mail__ = ("derek3x@vmail.me", "l.stickell@yahoo.it")


getInfo = create_getInfo(MegareleaseOrg)
