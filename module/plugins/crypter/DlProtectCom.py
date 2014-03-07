# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

import re
from base64 import urlsafe_b64encode
from time import time

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DlProtectCom(SimpleCrypter):
    __name__ = "DlProtectCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?dl-protect\.com/((en|fr)/)?(?P<ID>\w+)"
    __version__ = "0.01"
    __description__ = """dl-protect.com decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    OFFLINE_PATTERN = ">Unfortunately, the link you are looking for is not found"

    def getLinks(self):
        # Direct link with redirect
        if not re.match(r"http://(?:www\.)?dl-protect\.com", self.req.http.lastEffectiveURL):
            return [self.req.http.lastEffectiveURL]

        #id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        key = re.search(r'name="id_key" value="(.+?)"', self.html).group(1)

        post_req = {"id_key": key, "submitform": ""}

        if self.OFFLINE_PATTERN in self.html:
            self.offline()
        elif ">Please click on continue to see the content" in self.html:
            post_req.update({"submitform": "Continue"})
        else:
            mstime = int(round(time() * 1000))
            b64time = "_" + urlsafe_b64encode(str(mstime)).replace("=", "%3D")

            post_req.update({"i": b64time, "submitform": "Decrypt+link"})

            if ">Password :" in self.html:
                post_req["pwd"] = self.getPassword()

            if ">Security Code" in self.html:
                captcha_id = re.search(r'/captcha\.php\?uid=(.+?)"', self.html).group(1)
                captcha_url = "http://www.dl-protect.com/captcha.php?uid=" + captcha_id
                captcha_code = self.decryptCaptcha(captcha_url, imgtype="gif")

                post_req["secure"] = captcha_code

        self.html = self.load(self.pyfile.url, post=post_req)

        for errmsg in (">The password is incorrect", ">The security code is incorrect"):
            if errmsg in self.html:
                self.fail(errmsg[1:])

        pattern = r'<a href="([^/].+?)" target="_blank">'
        return re.findall(pattern, self.html)
