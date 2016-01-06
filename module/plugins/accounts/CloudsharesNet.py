# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class CloudsharesNet(XFSAccount):
    __name__    = "CloudsharesNet"
    __type__    = "account"
    __version__ = "0.02"
    __status__  = "testing"

    __description__ = """Cloudshares.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = "cloudshares.net"
