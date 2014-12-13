# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class SendmywayCom(XFSAccount):
    __name    = "SendmywayCom"
    __type    = "account"
    __version = "0.02"

    __description = """Sendmyway.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "sendmyway.com"
