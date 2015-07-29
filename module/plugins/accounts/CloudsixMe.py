# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class CloudsixMe(XFSAccount):
    __name__    = "CloudsixMe"
    __type__    = "account"
    __version__ = "0.01"
    __status__  = "testing"

    __description__ = """Cloudsix.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "cloudsix.me"
