# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount

class FilerioCom(XFSPAccount):
    __name__ = "FilerioCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """FileRio.in account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = "http://filerio.in/"