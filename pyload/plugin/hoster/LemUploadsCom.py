# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class LemUploadsCom(DeadHoster):
    __name    = "LemUploadsCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'https?://(?:www\.)?lemuploads\.com/\w{12}'
    __config  = []

    __description = """LemUploads.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
