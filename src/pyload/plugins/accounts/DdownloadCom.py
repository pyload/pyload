# -*- coding: utf-8 -*-

import pycurl

from ..base.xfs_account import XFSAccount


class DdownloadCom(XFSAccount):
    __name__ = "DdownloadCom"
    __type__ = "account"
    __version__ = "0.09"
    __status__ = "testing"

    __description__ = """Ddownload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"
    PLUGIN_URL = "http://ddownload.com"

    PREMIUM_PATTERN = r">Premium Member<"
    TRAFFIC_LEFT_PATTERN = r'available</div>\s*<div class="stat-card-value">\s*(?:<sup>(?P<U>[^<>]+)</sup>)?(?P<S>-?\d+|[Uu]nlimited)\s*</div>'
    VALID_UNTIL_PATTERN = r'class="expires">([\w ]+)<'

    def setup(self):
        super(DdownloadCom, self).setup()
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
