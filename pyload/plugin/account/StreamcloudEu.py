# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class StreamcloudEu(XFSAccount):
    __name__    = "StreamcloudEu"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Streamcloud.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "streamcloud.eu"
