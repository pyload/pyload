# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount


class BoltsharingCom(XFSPAccount):
    __name__ = "BoltsharingCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Boltsharing.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    MAIN_PAGE = "http://boltsharing.com/"
