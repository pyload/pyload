# -*- coding: utf-8 -*-

import re
import time

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


def convertDecimalPrefix(m):
    # decimal prefixes used in filesize and traffic
    return ("%%.%df" % {'k': 3, 'M': 6, 'G': 9}[m.group(2)] % float(m.group(1))).replace('.', '')


class UlozTo(SimpleHoster):
    __name__    = "UlozTo"
    __type__    = "hoster"
    __version__ = "1.09"

    __pattern__ = r'http://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl)/(?:live/)?(?P<ID>\w+/[^/?]*)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Uloz.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN    = r'<p>File <strong>(?P<N>[^<]+)</strong> is password protected</p>'
    NAME_PATTERN    = r'<title>(?P<N>[^<]+) \| Uloz\.to</title>'
    SIZE_PATTERN    = r'<span id="fileSize">.*?(?P<S>[\d.,]+\s[kMG]?B)</span>'
    OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'

    URL_REPLACEMENTS  = [(r'(?<=http://)([^/]+)', "www.ulozto.net")]
    SIZE_REPLACEMENTS = [(r'([\d.]+)\s([kMG])B', convertDecimalPrefix)]

    CHECK_TRAFFIC = True
    DISPOSITION   = False  #: Remove in 0.4.10

    ADULT_PATTERN   = r'<form action="(.+?)" method="post" id="frm-askAgeForm">'
    PASSWD_PATTERN  = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href=".+?\?disclaimer=1" class="linkVip">'
    TOKEN_PATTERN   = r'<input type="hidden" name="_token_" .*?value="(.+?)"'


    def setup(self):
        self.chunkLimit     = 16 if self.premium else 1
        self.multiDL        = True
        self.resumeDownload = True


    def handleFree(self, pyfile):
        action, inputs = self.parseHtmlForm('id="frm-downloadDialog-freeDownloadForm"')
        if not action or not inputs:
            self.error(_("Free download form not found"))

        self.logDebug("inputs.keys = " + str(inputs.keys()))
        # get and decrypt captcha
        if all(key in inputs for key in ("captcha_value", "captcha_id", "captcha_key")):
            # Old version - last seen 9.12.2013
            self.logDebug('Using "old" version')

            captcha_value = self.decryptCaptcha("http://img.uloz.to/captcha/%s.png" % inputs['captcha_id'])
            self.logDebug("CAPTCHA ID: " + inputs['captcha_id'] + ", CAPTCHA VALUE: " + captcha_value)

            inputs.update({'captcha_id': inputs['captcha_id'], 'captcha_key': inputs['captcha_key'], 'captcha_value': captcha_value})

        elif all(key in inputs for key in ("captcha_value", "timestamp", "salt", "hash")):
            # New version - better to get new parameters (like captcha reload) because of image url - since 6.12.2013
            self.logDebug('Using "new" version')

            xapca = self.load("http://www.ulozto.net/reloadXapca.php", get={'rnd': str(int(time.time()))})
            self.logDebug("xapca = " + str(xapca))

            data = json_loads(xapca)
            captcha_value = self.decryptCaptcha(str(data['image']))
            self.logDebug("CAPTCHA HASH: " + data['hash'], "CAPTCHA SALT: " + str(data['salt']), "CAPTCHA VALUE: " + captcha_value)

            inputs.update({'timestamp': data['timestamp'], 'salt': data['salt'], 'hash': data['hash'], 'captcha_value': captcha_value})

        else:
            self.error(_("CAPTCHA form changed"))

        self.download("http://www.ulozto.net" + action, post=inputs)


    def handlePremium(self, pyfile):
        self.download(pyfile.url, get={'do': "directDownload"})


    def checkErrors(self):
        if re.search(self.ADULT_PATTERN, self.html):
            self.logInfo(_("Adult content confirmation needed"))

            m = re.search(self.TOKEN_PATTERN, self.html)
            if m is None:
                self.error(_("TOKEN_PATTERN not found"))

            self.html = self.load(pyfile.url,
                                  get={'do': "askAgeForm-submit"},
                                  post={"agree": "Confirm", "_token_": m.group(1)})

        if self.PASSWD_PATTERN in self.html:
            password = self.getPassword()

            if password:
                self.logInfo(_("Password protected link, trying ") + password)
                self.html = self.load(pyfile.url,
                                      get={'do': "passwordProtectedForm-submit"},
                                      post={"password": password, "password_send": 'Send'})

                if self.PASSWD_PATTERN in self.html:
                    self.fail(_("Incorrect password"))
            else:
                self.fail(_("No password found"))

        if re.search(self.VIPLINK_PATTERN, self.html):
            self.html = self.load(pyfile.url, get={'disclaimer': "1"})

        return super(UlozTo, self).checkErrors()


    def checkFile(self, rules={}):
        check = self.checkDownload({
            "wrong_captcha": re.compile(r'<ul class="error">\s*<li>Error rewriting the text.</li>'),
            "offline"      : re.compile(self.OFFLINE_PATTERN),
            "passwd"       : self.PASSWD_PATTERN,
            "server_error" : 'src="http://img.ulozto.cz/error403/vykricnik.jpg"',  # paralell dl, server overload etc.
            "not_found"    : "<title>Ulož.to</title>"
        })

        if check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry(reason=_("Wrong captcha code"))

        elif check == "offline":
            self.offline()

        elif check == "passwd":
            self.fail(_("Wrong password"))

        elif check == "server_error":
            self.logError(_("Server error, try downloading later"))
            self.multiDL = False
            self.wait(1 * 60 * 60, True)
            self.retry()

        elif check == "not_found":
            self.fail(_("Server error, file not downloadable"))

        return super(UlozTo, self).checkFile(rules)


getInfo = create_getInfo(UlozTo)
