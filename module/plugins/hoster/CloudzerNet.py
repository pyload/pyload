# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class CloudzerNet(DeadHoster):
    __name__ = "CloudzerNet"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)\w+"
    __version__ = "0.05"
    __description__ = """Cloudzer.net hoster plugin"""
    __author_name__ = ("gs", "z00nx", "stickell")
    __author_mail__ = ("I-_-I-_-I@web.de", "z00nx0@gmail.com", "l.stickell@yahoo.it")


getInfo = create_getInfo(CloudzerNet)
