# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class FileApeCom(DeadHoster):
    __name__    = "FileApeCom"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'http://(?:www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+'

    __description__ = """FileApe.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("espes", "")]
