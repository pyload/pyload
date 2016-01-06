# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import json, timestamp


def convert_decimal_prefix(m):
    #: Decimal prefixes used in filesize and traffic
    return ("%%.%df" % {'k': 3, 'M': 6, 'G': 9}[m.group(2)] % float(m.group(1))).replace('.', '')


class UlozTo(SimpleHoster):
    __name__    = "UlozTo"
    __type__    = "hoster"
    __version__ = "1.19"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl)/(?:live/)?(?P<ID>\w+/[^/?]*)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Uloz.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'(<p>File <strong>|<title>)(?P<N>.+?)(<| \|)'
    SIZE_PATTERN    = r'<span id="fileSize">.*?(?P<S>[\d.,]+\s[kMG]?B)</span>'
    OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'

    URL_REPLACEMENTS  = [(r'(?<=http://)([^/]+)', "www.ulozto.net")]
    SIZE_REPLACEMENTS = [(r'([\d.]+)\s([kMG])B', convert_decimal_prefix)]

    CHECK_TRAFFIC = True

    ADULT_PATTERN   = r'<form action="(.+?)" method="post" id="frm-askAgeForm">'
    PASSWD_PATTERN  = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href=".+?\?disclaimer=1" class="linkVip">'
    TOKEN_PATTERN   = r'<input type="hidden" name="_token_" .*?value="(.+?)"'


    def setup(self):
        self.chunk_limit     = 16 if self.premium else 1
        self.multiDL        = True
        self.resume_download = True


    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('id="frm-downloadDialog-freeDownloadForm"')
        if not action or not inputs:
            self.error(_("Free download form not found"))

        self.log_debug("inputs.keys = %s" % inputs.keys())
        #: Get and decrypt captcha
        if all(key in inputs for key in ("captcha_value", "captcha_id", "captcha_key")):
            #: Old version - last seen 9.12.2013
            self.log_debug('Using "old" version')

            captcha_value = self.captcha.decrypt("http://img.uloz.to/captcha/%s.png" % inputs['captcha_id'])
            self.log_debug("CAPTCHA ID: " + inputs['captcha_id'] + ", CAPTCHA VALUE: " + captcha_value)

            inputs.update({'captcha_id': inputs['captcha_id'], 'captcha_key': inputs['captcha_key'], 'captcha_value': captcha_value})

        elif all(key in inputs for key in ("captcha_value", "timestamp", "salt", "hash")):
            #: New version - better to get new parameters (like captcha reload) because of image url - since 6.12.2013
            self.log_debug('Using "new" version')

            xapca = self.load("http://www.ulozto.net/reloadXapca.php",
                              get={'rnd': timestamp()})

            xapca = xapca.replace('sound":"', 'sound":"http:').replace('image":"', 'image":"http:')
            self.log_debug("xapca: %s" % xapca)

            data = json.loads(xapca)
            captcha_value = self.captcha.decrypt(data['image'])
            self.log_debug("CAPTCHA HASH: " + data['hash'], "CAPTCHA SALT: %s" % data['salt'], "CAPTCHA VALUE: " + captcha_value)

            inputs.update({'timestamp': data['timestamp'], 'salt': data['salt'], 'hash': data['hash'], 'captcha_value': captcha_value})

        else:
            self.error(_("CAPTCHA form changed"))

        self.download("http://www.ulozto.net" + action, post=inputs)


    def handle_premium(self, pyfile):
        self.download(pyfile.url, get={'do': "directDownload"})


    def check_errors(self):
        if re.search(self.ADULT_PATTERN, self.data):
            self.log_info(_("Adult content confirmation needed"))

            m = re.search(self.TOKEN_PATTERN, self.data)
            if m is None:
                self.error(_("TOKEN_PATTERN not found"))

            self.data = self.load(pyfile.url,
                                  get={'do': "askAgeForm-submit"},
                                  post={'agree': "Confirm", '_token_': m.group(1)})

        if self.PASSWD_PATTERN in self.data:
            password = self.get_password()

            if password:
                self.log_info(_("Password protected link, trying ") + password)
                self.data = self.load(pyfile.url,
                                      get={'do': "passwordProtectedForm-submit"},
                                      post={'password': password, 'password_send': 'Send'})

                if self.PASSWD_PATTERN in self.data:
                    self.fail(_("Wrong password"))
            else:
                self.fail(_("No password found"))

        if re.search(self.VIPLINK_PATTERN, self.data):
            self.data = self.load(pyfile.url, get={'disclaimer': "1"})

        return super(UlozTo, self).check_errors()


    def check_download(self):
        check = self.scan_download({
            'wrong_captcha': ">An error ocurred while verifying the user",
            'offline'      : re.compile(self.OFFLINE_PATTERN),
            'passwd'       : self.PASSWD_PATTERN,
            'server_error' : 'src="http://img.ulozto.cz/error403/vykricnik.jpg"',  #: Paralell dl, server overload etc.
            'not_found'    : "<title>Ulož.to</title>"
        })

        if check == "wrong_captcha":
            self.retry_captcha()

        elif check == "offline":
            self.offline()

        elif check == "passwd":
            self.fail(_("Wrong password"))

        elif check == "server_error":
            self.log_error(_("Server error, try downloading later"))
            self.multiDL = False
            self.wait(1 * 60 * 60, True)
            self.retry()

        elif check == "not_found":
            self.fail(_("Server error, file not downloadable"))

        return super(UlozTo, self).check_download()
