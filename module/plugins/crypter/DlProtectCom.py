# -*- coding: utf-8 -*-

import re
import time

from base64 import urlsafe_b64encode

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class DlProtectCom(SimpleCrypter):
    __name__    = "DlProtectCom"
    __type__    = "crypter"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?dl-protect\.com/((en|fr)/)?\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Dl-protect.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("dl-protect.com", "l", "en")]

    OFFLINE_PATTERN = r'Unfortunately, the link you are looking for is not found'


    def get_links(self):
        #: Direct link with redirect
        if not re.match(r"https?://(?:www\.)?dl-protect\.com/.+", self.req.http.lastEffectiveURL):
            return [self.req.http.lastEffectiveURL]

        post_req = {'key'       : re.search(r'name="key" value="(.+?)"', self.html).group(1),
                    'submitform': ""}

        if "Please click on continue to see the links" in self.html:
            post_req['submitform'] = "Continue"
            self.wait(2)

        else:
            mstime  = int(round(time.time() * 1000))
            b64time = "_" + urlsafe_b64encode(str(mstime)).replace("=", "%3D")

            post_req.update({'i'         : b64time,
                             'submitform': "Decrypt+link"})

            if "Password :" in self.html:
                post_req['pwd'] = self.get_password()

            if "Security Code" in self.html:
                m = re.search(r'/captcha\.php\?key=(.+?)"', self.html)
                if m:
                    captcha_code = self.captcha.decrypt("http://www.dl-protect.com/captcha.php?key=" + m.group(1), input_type="gif")
                    post_req['secure'] = captcha_code

        self.html = self.load(self.pyfile.url, post=post_req)

        for errmsg in ("The password is incorrect", "The security code is incorrect"):
            if errmsg in self.html:
                self.fail(_(errmsg[1:]))

        return re.findall(r'<a href="([^/].+?)" target="_blank">', self.html)


getInfo = create_getInfo(DlProtectCom)
