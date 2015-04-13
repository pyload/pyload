# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class StreamcloudEu(XFSAccount):
    __name    = "StreamcloudEu"
    __type    = "account"
    __version = "0.02"

    __description = """Streamcloud.eu account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "streamcloud.eu"
