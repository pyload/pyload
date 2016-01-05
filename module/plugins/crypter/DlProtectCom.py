# -*- coding: utf-8 -*-

import base64
import re
import time

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DlProtectCom(SimpleCrypter):
    __name__    = "DlProtectCom"
    __type__    = "crypter"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?dl-protect\.com/((en|fr)/)?\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Dl-protect.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("dl-protect.com", "l", "en")]

    OFFLINE_PATTERN = r'Unfortunately, the link you are looking for is not found'


    # Information decoding
    # For test purposes
    def info_decode(self, i):
        # Remove end string
        assert i.endswith("_%3D")
        i = i[0:-4]
        # Invert string
        i = i[::-1]
        # Base 64 decode
        i = base64.b64decode(i)
        # Split information
        infos = i.split('|')
        assert(len(infos) == 4)
        res = infos[0]
        user_agent = infos[1]
        plugins = [x.split(';') for x in infos[2].split('&')]
        java = {"ENABLE": True, "DISABLE":False}[infos[3]]
        # Return information
        return {'res':res,
                'user_agent':user_agent,
                'plugins':plugins,
                'java':java}

    # Information encoding
    def info_encode(self, info):
        # Pack information
        res = info['res']
        user_agent = info['user_agent']
        plugins = '&'.join(';'.join(x) for x in info['plugins'])
        java = {True:"ENABLE", False:"DISABLE"}[info['java']]
        i = '|'.join([res, user_agent, plugins, java])
        # Base 64 encode
        i = base64.b64encode(i)
        # Invert string
        i = i[::-1]
        # Add end string and return
        i = i + "_%3D"
        return i

    # Sample configuration
    def conf(self):
        useragent = self.pyload.api.getConfigValue("UserAgentSwitcher", "useragent", "plugin")
        conf = {'res': '1280x611x24',
                'java': True,
                'user_agent': useragent,
                'plugins': [['Adobe Acrobat', 'nppdf32.dll', 'Adobe PDF Plug-In For Firefox and Netscape 11.0.13', '11.0.13.17'],
                            ['Adobe Acrobat', 'nppdf32.dll', 'Adobe PDF Plug-In For Firefox and Netscape 11.0.13', '11.0.13.17'],
                            ['Java(TM) Platform SE 8 U51', 'npjp2.dll', 'Next Generation Java Plug-in 11.51.2 for Mozilla browsers', '11.51.2.16'],
                            ['Shockwave Flash', 'NPSWF32_19_0_0_226.dll', 'Shockwave Flash 19.0 r0', '19.0.0.226']]}
        return conf

    def get_links(self):
        #: Direct link with redirect
        if not re.match(r'https?://(?:www\.)?dl-protect\.com/.+', self.req.http.lastEffectiveURL):
            return [self.req.http.lastEffectiveURL]

        post_req = {'key'       : re.search(r'name="key" value="(.+?)"', self.data).group(1),
                    'submitform': ""}
        self.log_debug("Key: %s" % post_req['key'])

        if "Please click on continue to see the links" in self.data:
            post_req['submitform'] = "Continue"
            post_req['i'] = self.info_encode(self.conf())
            self.wait(2)

        else:
            mstime  = int(round(time.time() * 1000))
            b64time = "_" + base64.urlsafe_b64encode(str(mstime)).replace("=", "%3D")

            post_req.update({'i'         : b64time,
                             'submitform': "Decrypt+link"})

            if "Password :" in self.data:
                post_req['pwd'] = self.get_password()

            if "Security Code" in self.data:
                m = re.search(r'/captcha\.php\?key=(.+?)"', self.data)
                if m is not None:
                    captcha_code = self.captcha.decrypt("http://www.dl-protect.com/captcha.php?key=" + m.group(1), input_type="gif")
                    self.log_debug("Captcha code: %s" % captcha_code)
                    post_req['secure'] = captcha_code
                else:
                    self.log_debug("Captcha code requested but captcha not found")

        self.data = self.load(self.pyfile.url, post=post_req)

        # Check error messages in pages
        for errmsg in ("The password is incorrect", "The security code is incorrect"):
            if errmsg in self.data:
                self.fail(_(errmsg[1:]))

        # Filters interesting urls from ads
        return re.findall(r'<a href="(?P<id>[^/].+?)" target="_blank">(?P=id)</a>', self.data)
