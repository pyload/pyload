# -*- coding: utf-8 -*-

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.captcha.SolveMedia import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MediafireCom(SimpleHoster):
    __name__    = "MediafireCom"
    __type__    = "hoster"
    __version__ = "0.90"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?mediafire\.com/(file/|view/\??|download(\.php\?|/)|\?)(?P<ID>\w{15})'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Mediafire.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<META NAME="description" CONTENT="(?P<N>.+?)"/>'
    SIZE_PATTERN    = r'<li>File size: <span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    INFO_PATTERN    = r'oFileSharePopup\.ald\(\'.*?\',\'(?P<N>.+?)\',\'(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)\',\'\',\'(?P<H>.+?)\'\)'
    OFFLINE_PATTERN = r'class="error_msg_title"'

    LINK_FREE_PATTERN = r'kNO = "(.+?)"'

    PASSWORD_PATTERN = r'<form name="form_password"'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def handle_captcha(self):
        solvemedia  = SolveMedia(self)
        captcha_key = solvemedia.detect_key()

        if captcha_key:
            response, challenge = solvemedia.challenge(captcha_key)
            self.html = self.load("http://www.mediafire.com/?" + self.info['pattern']['ID'],
                                  post={'adcopy_challenge': challenge,
                                        'adcopy_response' : response})
            return

        recaptcha   = ReCaptcha(self)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            response, challenge = recaptcha.challenge(captcha_key)
            self.html = self.load(self.pyfile.url,
                                  post={'g-recaptcha-response': response})


    def handle_free(self, pyfile):
        self.handle_captcha()

        if self.PASSWORD_PATTERN in self.html:
            password = self.get_password()

            if not password:
                self.fail(_("No password found"))
            else:
                self.log_info(_("Password protected link, trying: ") + password)
                self.html = self.load(self.link, post={'downloadp': password})

                if self.PASSWORD_PATTERN in self.html:
                    self.fail(_("Incorrect password"))

        return super(MediafireCom, self).handle_free(pyfile)


getInfo = create_getInfo(MediafireCom)
