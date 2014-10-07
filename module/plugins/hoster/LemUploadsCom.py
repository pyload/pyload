# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class LemUploadsCom(DeadHoster):
    __name__ = "LemUploadsCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?lemuploads\.com/\w{12}'

    __description__ = """LemUploads.com hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"


getInfo = create_getInfo(LemUploadsCom)
