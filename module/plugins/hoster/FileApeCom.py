#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FileApeCom(DeadHoster):
    __name__ = "FileApeCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?fileape\.com/(index\.php\?act=download&id=|dl/)(?P<ID>\w+)"
    __version__ = "0.12"
    __description__ = """FileApe Download Hoster"""
    __author_name__ = ("espes")


getInfo = create_getInfo(FileApeCom)
