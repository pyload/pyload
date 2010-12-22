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

from module.plugins.Account import Account
import re
from time import strptime, mktime
from cookielib import Cookie

class UploadedTo(Account):
    __name__ = "UploadedTo"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """ul.to account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):
        html = req.getPage("http://uploaded.to/", cookies=True)
        raw_traffic = re.search(r"Traffic left: </span><span class=.*?>(.*?)</span>", html).group(1)
        raw_valid = re.search(r"Valid until: </span> <span class=.*?>(.*?)</span>", html).group(1)
        traffic = int(self.parseTraffic(raw_traffic))
        validuntil = int(mktime(strptime(raw_valid.strip(), "%d-%m-%Y %H:%M")))
    
        tmp =  {"validuntil":validuntil, "trafficleft":traffic, "maxtraffic":100*1024*1024}
        return tmp

    def login(self, user, data, req):
        req.cookieJar.set_cookie(Cookie(version=0, name='lang', value='en', port=None, port_specified=False, domain='.uploaded.to', domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=None, discard=False, comment=None, comment_url=None, rest={}, rfc2109=False))
        page = req.getPage("http://uploaded.to/login", post={ "email" : user, "password" : data["password"]})
        if "Login failed!" in page:
            self.wrongPassword()
