# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount

class DdlstorageCom(XFSPAccount):
    __name__ = "DdlstorageCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """DDLStorage.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = "http://ddlstorage.com/"