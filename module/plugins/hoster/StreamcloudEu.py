# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class StreamcloudEu(XFSHoster):
    __name__    = "StreamcloudEu"
    __type__    = "hoster"
    __version__ = "0.10"

    __pattern__ = r'http://(?:www\.)?streamcloud\.eu/\w{12}'

    __description__ = """Streamcloud.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("seoester", "seoester@googlemail.com")]


    HOSTER_DOMAIN = "streamcloud.eu"

    WAIT_PATTERN = r'var count = (\d+)'

    LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud\.eu:?\d*/.*/video\.(mp4|flv))",'


    def setup(self):
        self.multiDL        = True
        self.chunkLimit     = 1
        self.resumeDownload = self.premium


getInfo = create_getInfo(StreamcloudEu)
