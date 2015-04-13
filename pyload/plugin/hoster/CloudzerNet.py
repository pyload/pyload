# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class CloudzerNet(DeadHoster):
    __name    = "CloudzerNet"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://(?:www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)\w+'
    __config  = []

    __description = """Cloudzer.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("gs", "I-_-I-_-I@web.de"),
                       ("z00nx", "z00nx0@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]
