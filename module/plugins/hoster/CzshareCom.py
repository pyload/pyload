# -*- coding: utf-8 -*-
#
# Test links:
# http://czshare.com/5278880/random.bin

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import parseFileSize as parse_size


class CzshareCom(SimpleHoster):
    __name__    = "CzshareCom"
    __type__    = "hoster"
    __version__ = "1.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(czshare|sdilej)\.(com|cz)/(\d+/|download\.php\?).+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """CZshare.com hoster plugin, now Sdilej.cz"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<div class="tab" id="parameters">\s*<p>\s*Cel. n.zev: <a href=.*?>(?P<N>[^<]+)</a>'
    SIZE_PATTERN    = r'<div class="tab" id="category">(?:\s*<p>[^\n]*</p>)*\s*Velikost:\s*(?P<S>[\d .,]+)(?P<U>[\w^_]+)\s*</div>'
    OFFLINE_PATTERN = r'<div class="header clearfix">\s*<h2 class="red">'

    SIZE_REPLACEMENTS = [(' ', '')]
    URL_REPLACEMENTS  = [(r'http://[^/]*/download.php\?.*?id=(\w+).*', r'http://sdilej.cz/\1/x/')]

    CHECK_TRAFFIC = True

    FREE_URL_PATTERN     = r'<a href="(.+?)" class="page-download">[^>]*alt="(.+?)" /></a>'
    FREE_FORM_PATTERN    = r'<form action="download\.php" method="post">\s*<img src="captcha\.php" id="captcha" />(.*?)</form>'
    PREMIUM_FORM_PATTERN = r'<form action="/profi_down\.php" method="post">(.*?)</form>'
    FORM_INPUT_PATTERN   = r'<input[^>]* name="(.+?)" value="(.+?)"[^>]*/>'
    MULTIDL_PATTERN      = r'<p><font color=\'red\'>Z[^<]*PROFI.</font></p>'
    USER_CREDIT_PATTERN  = r'<div class="credit">\s*kredit: <strong>([\d .,]+)(\w+)</strong>\s*</div><!-- .credit -->'


    def check_traffic_left(self):
        #: Check if user logged in
        m = re.search(self.USER_CREDIT_PATTERN, self.html)
        if m is None:
            self.account.relogin(self.user)
            self.html = self.load(self.pyfile.url)
            m = re.search(self.USER_CREDIT_PATTERN, self.html)
            if m is None:
                return False

        #: Check user credit
        try:
            credit = parse_size(m.group(1).replace(' ', ''), m.group(2))
            self.log_info(_("Premium download for %i KiB of Credit") % (self.pyfile.size / 1024))
            self.log_info(_("User %s has %i KiB left") % (self.user, credit / 1024))
            if credit < self.pyfile.size:
                self.log_info(_("Not enough credit to download file: %s") % self.pyfile.name)
                return False
        except Exception, e:
            #: let's continue and see what happens...
            self.log_error(e)

        return True


    def handle_premium(self, pyfile):
    #: Parse download link
        try:
            form = re.search(self.PREMIUM_FORM_PATTERN, self.html, re.S).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.log_error(e)
            self.restart(nopremium=True)

        #: Download the file, destination is determined by pyLoad
        self.download("http://sdilej.cz/profi_down.php", post=inputs, disposition=True)


    def handle_free(self, pyfile):
        #: Get free url
        m = re.search(self.FREE_URL_PATTERN, self.html)
        if m is None:
            self.error(_("FREE_URL_PATTERN not found"))

        parsed_url = "http://sdilej.cz" + m.group(1)

        self.log_debug("PARSED_URL:" + parsed_url)

        #: Get download ticket and parse html
        self.html = self.load(parsed_url)
        if re.search(self.MULTIDL_PATTERN, self.html):
            self.wait(5 * 60, 12, _("Download limit reached"))

        try:
            form = re.search(self.FREE_FORM_PATTERN, self.html, re.S).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.size = int(inputs['size'])

        except Exception, e:
            self.log_error(e)
            self.error(_("Form"))

        #: Get and decrypt captcha
        captcha_url = 'http://sdilej.cz/captcha.php'
        for _i in xrange(5):
            inputs['captchastring2'] = self.captcha.decrypt(captcha_url)
            self.html = self.load(parsed_url, post=inputs)

            if u"<li>Zadaný ověřovací kód nesouhlasí!</li>" in self.html:
                self.captcha.invalid()

            elif re.search(self.MULTIDL_PATTERN, self.html):
                self.wait(5 * 60, 12, _("Download limit reached"))

            else:
                self.captcha.correct()
                break
        else:
            self.fail(_("No valid captcha code entered"))

        m = re.search("countdown_number = (\d+);", self.html)
        self.set_wait(int(m.group(1)) if m else 50)

        #: Download the file, destination is determined by pyLoad
        self.log_debug("WAIT URL", self.req.lastEffectiveURL)

        m = re.search("free_wait.php\?server=(.*?)&(.*)", self.req.lastEffectiveURL)
        if m is None:
            self.error(_("Download URL not found"))

        self.link = "http://%s/download.php?%s" % (m.group(1), m.group(2))

        self.wait()


    def check_file(self):
        #: Check download
        check = self.check_download({
            "temp offline" : re.compile(r"^Soubor je do.*asn.* nedostupn.*$"),
            'credit'       : re.compile(r"^Nem.*te dostate.*n.* kredit.$"),
            "multi-dl"     : re.compile(self.MULTIDL_PATTERN),
            'captcha'      : "<li>Zadaný ověřovací kód nesouhlasí!</li>"
        })

        if check == "temp offline":
            self.fail(_("File not available - try later"))

        elif check == "credit":
            self.restart(nopremium=True)

        elif check == "multi-dl":
            self.wait(5 * 60, 12, _("Download limit reached"))

        elif check == "captcha":
            self.captcha.invalid()
            self.retry()

        return super(CzshareCom, self).check_file()


getInfo = create_getInfo(CzshareCom)
