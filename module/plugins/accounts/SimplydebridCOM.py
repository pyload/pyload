# -*- coding: utf-8 -*-
from module.plugins.Account import Account

import re
from time import mktime, strptime

class SimplydebridCOM(Account):
	__name__ = "SimplydebridCOM"
	__version__ = "0.1"
	__type__ = "account"
	__description__ = """Simply-Debrid.com account plugin"""
	__author_name__ = ("Kagenoshin")
	__author_mail__ = ("kagenoshin@gmx.ch")    
	
	def loadAccountInfo(self, user, req):
		get_data = {
		}
		response = req.load("http://simply-debrid.com/api.php?login=2&u="+self.loginname+"&p="+self.password, get = get_data, decode = True, just_header = False)
		if(response[len(response)-1] == ";"): #remove ; if the v entry ends with ;
			response = response[0:len(response)-1]
		data = [x.strip() for x in response.split(";")]
		if str(data[0]) != "1":
			account_info = {"trafficleft": 0, "validuntil": 0, "premium": False}
		else:
			account_info = {
				"trafficleft": -1,
				"validuntil": mktime(strptime(str(data[2]),"%d/%m/%Y")),
				"premium": True         
			}
		return account_info

	def login(self, user, data, req):
		self.loginname = user
		self.password = data["password"]
		get_data = {
		}
		response = req.load("http://simply-debrid.com/api.php?login=1&u="+self.loginname+"&p="+self.password, get = get_data, decode = True, just_header = False) 
		if response != "02: loggin success":
			self.wrongPassword()