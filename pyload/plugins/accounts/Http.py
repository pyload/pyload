# -*- coding: utf-8 -*-

from module.plugins.Account import Account

class Http(Account):
    __name__ = "Http"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Http dummy account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    login_timeout = info_threshold = 1000000