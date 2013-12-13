#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ShragleCom(DeadHoster):
    __name__ = "ShragleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?(cloudnator|shragle).com/files/(?P<ID>.*?)/"
    __version__ = "0.22"
    __description__ = """Cloudnator.com (Shragle.com) Download PLugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")


getInfo = create_getInfo(ShragleCom)
