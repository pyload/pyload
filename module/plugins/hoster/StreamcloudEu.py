# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class StreamcloudEu(XFSHoster):
    __name__    = "StreamcloudEu"
    __type__    = "hoster"
    __version__ = "0.11"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?streamcloud\.eu/\w{12}'

    __description__ = """Streamcloud.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("seoester", "seoester@googlemail.com")]


    WAIT_PATTERN = r'var count = (\d+)'


    def setup(self):
        self.multiDL        = True
        self.chunk_limit     = 1
        self.resume_download = self.premium


getInfo = create_getInfo(StreamcloudEu)
