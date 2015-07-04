# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingLite import XFileSharingLite, create_getInfo


class ThevideoMe(XFileSharingLite):
    __name__ = "ThevideoMe"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:\w*\.)*(?P<DOMAIN>thevideo\.me)/"
    __version__ = "0.01"
    __description__ = """thevideo.me plugin"""
    __author_name__ = ("igel")
    __author_mail__ = ("")

    HIDDEN_POST_PARAMETERS = "attr.*id: '(?P<id>[^']*)'.*value: '(?P<value>[^']*)'.*prependTo\(.*form.*\)"



getInfo = create_getInfo(ThevideoMe)
