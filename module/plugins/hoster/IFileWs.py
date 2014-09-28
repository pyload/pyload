# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IFileWs(DeadHoster):
    __name__ = "IFileWs"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?ifile\.ws/\w{12}'

    __description__ = """Ifile.ws hoster plugin"""
    __author_name__ = "z00nx"
    __author_mail__ = "z00nx0@gmail.com"


getInfo = create_getInfo(IFileWs)
