# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class CloudzerNet(DeadHoster):
    __name__    = "CloudzerNet"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Cloudzer.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("gs", "I-_-I-_-I@web.de"),
                       ("z00nx", "z00nx0@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(CloudzerNet)
