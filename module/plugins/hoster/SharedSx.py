# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class SharedSx(XFileSharingPro):
    __name__ = "SharedSx"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:\w*\.)*(?P<DOMAIN>shared\.sx)/"
    __version__ = "0.01"
    __description__ = """shared.sx plugin"""
    __author_name__ = ("igel")
    __author_mail__ = ("")

    HOSTERDOMAIN = 'shared.sx'
    # FORM_PATTERN = r'<form\s*method="post">(.*?>Continue to file<.*?)</form>'
    FORM_PATTERN = 'method'
    INFO_PATTERN = '<h1 data-hash.*?>\w* (?P<N>[^<]+)<strong>\((?P<S>[\d.]+) (?P<U>\w+)\)</strong>'
    WAIT_TIME = r'var countdownNum = (\d+)'
    # if called without DOTALL, we need this:
    #DIRECT_LINK_PATTERN = r'jwplayer(?:.|\n)*?file: "([^"]*)"'
    LINK_PATTERN = r'data-url="([^"]*)"'

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

getInfo = create_getInfo(SharedSx)
