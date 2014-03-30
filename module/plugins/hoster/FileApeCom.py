#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FileApeCom(DeadHoster):
    __name__ = "FileApeCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+"
    __version__ = "0.12"
    __description__ = """FileApe.com hoster plugin"""
    __author_name__ = "espes"
    __author_mail__ = ""


getInfo = create_getInfo(FileApeCom)
