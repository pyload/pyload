#!/usr/bin/env python
# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount


class ShareFilesCo(XFSPAccount):
    __name__ = "ShareFilesCo"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """ShareFilesCo account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    MAIN_PAGE = "http://sharefiles.co/"
