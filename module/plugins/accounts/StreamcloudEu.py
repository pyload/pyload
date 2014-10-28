# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class StreamcloudEu(XFSPAccount):
    __name__    = "StreamcloudEu"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """Streamcloud.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "streamcloud.eu"
