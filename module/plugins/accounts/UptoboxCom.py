# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
	__name__    = "UptoboxCom"
	__type__    = "account"
	__version__ = "0.12"
	__status__  = "testing"

	__description__ = "Uptobox.com account plugin"
	__license__     = "GPLv3"
	__authors__     = [("benbox69", "dev@tollet.me")]


	HOSTER_DOMAIN = "uptobox.com"
	HOSTER_URL    = "https://uptobox.com/"
	LOGIN_URL     = "https://login.uptobox.com/logarithme"

	def login(self, user, password, data, req):

		jsonstring = self.load(self.LOGIN_URL, None,  post={'login': user, 'password': password, 'op': 'login'})
		
		parsedjson = json.loads(jsonstring)
		
		if parsedjson['success'] is None:
			self.login_fail()
