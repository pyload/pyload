# -*- coding: utf-8 -*-

import json
import re
import time

from module.plugins.internal.Account import Account


class UptoboxCom(Account):
	__name__    = "UptoboxCom"
	__type__    = "account"
	__version__ = "0.10"
	__status__  = "testing"

	__description__ = """Uptobox.com account plugin"""
	__license__     = "GPLv3"
	__authors__     = [("benbox69", "dev@tollet.me")]


	HOSTER_DOMAIN = "uptobox.com"
	HOSTER_URL    = "https://uptobox.com/"
	LOGIN_URL     = "https://login.uptobox.com/logarithme"

	VALID_UNTIL_PATTERN = r'Premium-Account expire: (\d{1,2} [\w^_]+ \d{4})'

	def parse_info(self, user, password, data, req):

		validuntil   = None
        	trafficleft  = None
       		premium      = None

		data = self.get_data(user)
		html = self.load(self.HOSTER_URL, get={'op': "my_account"})

		p = re.compile(self.VALID_UNTIL_PATTERN)
		
		m = re.search(p, html)

		if m:
			expiredate = m.group(1).strip()
			self.log_debug("Expire date: " + expiredate)

            		try:
                		validuntil = time.mktime(time.strptime(expiredate, "%d %B %Y"))

            		except Exception, e:
                		self.log_error(e)

            		else:
                		self.log_debug("Valid until: %s" % validuntil)

                		if validuntil > time.mktime(time.gmtime()):
                    			premium     = True
                    			trafficleft = -1
                		else:
                    			premium    = False
                    			validuntil = None  #: Registered account type (not premium)
        	else:
            		self.log_debug("VALID_UNTIL_PATTERN not found")

		return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


	def login(self, user, password, data, req):

		jsonstring = self.load(self.LOGIN_URL, None,  post={'login': user, 'password': password, 'op': 'login'})
		
		parsedjson = json.loads(jsonstring)
		
		if parsedjson['success'] is None:
			self.login_fail()
