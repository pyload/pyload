# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class StreamcloudEu(XFSPAccount):
    __name__ = "StreamcloudEu"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Streamcloud.eu account plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"


    HOSTER_URL = "http://www.streamcloud.eu/"
