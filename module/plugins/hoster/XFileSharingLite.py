# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class XFileSharingLite(XFileSharingPro):
    __name__ = "XFileSharingLite"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(?P<DOMAIN>vodlocker.com|played.to|faststream.in)/\w{12}"
    __version__ = "0.01"
    __description__ = """XFileSharingLite plugin"""
    __author_name__ = ("igel")
    __author_mail__ = ("")

    WAIT_TIME = r'var countdownNum = (\d+)'
    # if called without DOTALL, we need this:
    #LINK_PATTERN = r'jwplayer(?:.|\n)*?file: "([^"]*)"'
    # with DOTALL, do this:
    LINK_PATTERN = "jwplayer.*?['\"]?file['\"]?\s*: ['\"]([^'\"]*)['\"]"

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

getInfo = create_getInfo(XFileSharingLite)
