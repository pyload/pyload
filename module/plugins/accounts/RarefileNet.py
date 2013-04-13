# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount

class RarefileNet(XFSPAccount):
    __name__ = "RarefileNet"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """RareFile.net account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = "http://rarefile.net/"
