# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ShareRapidCom(DeadHoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?((share(-?rapid\.(biz|com|cz|eu|info|net|org|pl|sk)|-(central|credit|free|net)\.cz|-ms\.net)|(s-?rapid|rapids)\.(cz|sk))|(e-stahuj|mediatack|rapidspool|premium-rapidshare|rapidshare-premium|qiuck)\.cz|(kadzet|jirkasekyrka|universal-share)\.com|stahuj-zdarma\.eu|strelci\.net)/stahuj/\w+"
    __version__ = "0.54"
    __description__ = """Share-rapid.com hoster plugin"""
    __author_name__ = ("MikyWoW", "zoidberg", "stickell")
    __author_mail__ = ("MikyWoW@seznam.cz", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")


getInfo = create_getInfo(ShareRapidCom)
