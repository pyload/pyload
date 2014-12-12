# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FileApeCom(DeadHoster):
    __name    = "FileApeCom"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+'

    __description = """FileApe.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("espes", "")]


getInfo = create_getInfo(FileApeCom)
