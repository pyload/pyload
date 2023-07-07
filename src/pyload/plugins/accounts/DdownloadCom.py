# -*- coding: utf-8 -*-

import pycurl

from ..base.xfs_account import XFSAccount


class DdownloadCom(XFSAccount):
    __name__ = "DdownloadCom"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Ddownload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"
    PLUGIN_URL = "http://ddownload.com"

    PREMIUM_PATTERN = r"Premium Account \(expires"
    TRAFFIC_LEFT_PATTERN = r'<span>Traffic available</span>\s*<div class="price">(?:<sup>(?P<U>[^<>]+)</sup>)?(?P<S>-?\d+|[Uu]nlimited)</div>'
    VALID_UNTIL_PATTERN = r"Premium Account \(expires ([^)]+)\)"

    def setup(self):
        super(DdownloadCom, self).setup()
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
