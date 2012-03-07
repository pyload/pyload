from module.plugins.Account import Account
import xml.dom.minidom as dom
from time import time

class AlldebridCom(Account):
    __name__ = "AlldebridCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """AllDebrid.com account plugin"""
    __author_name__ = ("Andy, Voigt")
    __author_mail__ = ("spamsales@online.de")

    def loadAccountInfo(self, user, req):
		data = self.getAccountData(user)
		page = req.load("http://www.alldebrid.com/api.php?action=info_user&login=%s&pw=%s" %  (user, data["password"]))
		self.log.debug(page)
		xml = dom.parseString(page)
		account_info = {"validuntil": (time()+int(xml.getElementsByTagName("date")[0].childNodes[0].nodeValue)*86400),
                        "trafficleft": -1}

		return account_info

    def login(self, user, data, req):      
		page = req.load("http://www.alldebrid.com/register/?action=login&login_login=%s&login_password=%s" % (user, data["password"]))
		
		if "This login doesn't exist" in page:
			self.wrongPassword()
