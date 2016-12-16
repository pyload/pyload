# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.plugin.hoster import Hoster as _Hoster


def create_get_info(plugin):
    def get_info(urls):
        yield [('#N/A: ' + url, 0, 1, url) for url in urls]
    return getInfo


class DeadHoster(_Hoster):
    __name__ = "DeadHoster"
    __type__ = "hoster"
    __pattern__ = None
    __version__ = "0.11"
    __description__ = """Hoster is no longer available"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def setup(self):
        self.fail("Hoster is no longer available")
