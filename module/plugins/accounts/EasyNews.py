# -*- coding: utf-8 -*-

from module.plugins.Account import Account

class EasyNews(Account):
    __name__ = "EasyNews"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """EasyNews account login"""
    __author_name__ = ("seb")
    __author_mail__ = ("pyload@seb.so")
    
    login_timeout = info_threshold = 1000000

    def loadAccountInfo(self, name, req=None):
        return {
            "login": name,
            "password": self.accounts[name]["password"],
            "timestamp": 0, #time this info was retrieved
            "type": self.__name__,
            }
    
