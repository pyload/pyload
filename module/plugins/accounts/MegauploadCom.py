# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay
"""

import re
from time import time

from module.plugins.Account import Account

class MegauploadCom(Account):
    __name__ = "MegauploadCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """megaupload account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def loadAccountInfo(self, user, req):
        page = req.load("http://www.megaupload.com/?c=account")

        free = re.findall(r"Account type:\s*</div>\s*<div class=\"acc_txt_bl2\">\s*<b>Regular</b>",page,re.IGNORECASE+re.MULTILINE)
        if free:
            return {"validuntil": -1, "trafficleft":-1, "premium": False}

        if 'id="directdownloadstxt">Activate' in page:
            self.core.log.warning(_("Activate direct Download in your MegaUpload Account"))

        valid = re.search(r"(\d+) days remaining", page).group(1)
        valid = time()+ 60 * 60 * 24 * int(valid)

        return {"validuntil": valid, "trafficleft": -1, "premium": True}


    def login(self, user, data, req):
        page = req.load("http://www.megaupload.com/?c=login&next=c%3Dpremium", post={ "username" : user, "password" : data["password"], "login" :"1"}, cookies=True)
        if "Username and password do not match" in page:
            self.wrongPassword()
