#!/usr/bin/env python
# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class TusfilesNet(XFileSharingPro):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?tusfiles\.net/(?P<ID>[a-zA-Z0-9]{12})"
    __version__ = "0.02"
    __description__ = """Tusfiles.net hoster plugin"""
    __author_name__ = ("stickell", "Walter Purcaro")
    __author_mail__ = ("l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<li>(?P<N>[^<]+)</li>\s+<li><b>Size:</b> <small>(?P<S>[\d.]+) (?P<U>\w+)</small></li>'
    FILE_OFFLINE_PATTERN = r'The file you were looking for could not be found'
    HOSTER_NAME = "tusfiles.net"

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.multiDL = True
        if self.premium:
            self.limitDL = 5
        elif self.account:
            self.limitDL = 3
        else:
            self.limitDL = 2


getInfo = create_getInfo(TusfilesNet)
