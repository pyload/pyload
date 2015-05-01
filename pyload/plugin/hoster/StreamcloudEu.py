# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class StreamcloudEu(XFSHoster):
    __name    = "StreamcloudEu"
    __type    = "hoster"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?streamcloud\.eu/\w{12}'

    __description = """Streamcloud.eu hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("seoester", "seoester@googlemail.com")]


    WAIT_PATTERN = r'var count = (\d+)'

    LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud\.eu:?\d*/.*/video\.(mp4|flv))",'


    def setup(self):
        self.multiDL        = True
        self.chunkLimit     = 1
        self.resumeDownload = self.premium
