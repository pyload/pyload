# -*- coding: utf-8 -*-

from module.plugins.accounts.FilejungleCom import FilejungleCom

class UploadstationCom(FilejungleCom):
    __name__ = "UploadstationCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """uploadstation.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    URL = "http://uploadstation.com/"
