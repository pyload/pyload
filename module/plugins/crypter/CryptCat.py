# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class CryptCat(SimpleCrypter):
    __name__    = "CryptCat"
    __type__    = "crypter"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?crypt\.cat/\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """crypt.cat decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    OFFLINE_PATTERN = r'Folder not available!'

    LINK_PATTERN    = r'<input .+?readonly="" value="\s*(.+?)" type="text">'


    def get_links(self):
        url = self.req.http.lastEffectiveURL

        if ">Enter your password.<" in self.data:
            password = self.get_password()
            if not password:
                self.fail(_("Password required"))

            post_data = {'Pass1'   : password,
                         'Submit0' : "" }

        elif "Enter Captcha" in self.data:
            m = re.search(r'<img src="(.+?)"', self.data)
            if m:
                captcha_code = self.captcha.decrypt(m.group(1), input_type="jpeg")
                post_data = {'security_code' : captcha_code,
                             'submit1'       : "" }
            else:
                return []

        else:
            return []

        self.data = self.load(url, post=post_data, ref=url)

        if "You have entered an incorrect password." in self.data:
            self.fail(_("Wrong password"))

        elif "Your filled the captcha wrongly!" in self.data:
            self.retry_captcha()

        return re.findall(self.LINK_PATTERN, self.data)
