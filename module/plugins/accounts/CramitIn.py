# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount

class CramitIn(XFSPAccount):
    __name__ = "CramitIn"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """cramit.in account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = "http://cramit.in/"