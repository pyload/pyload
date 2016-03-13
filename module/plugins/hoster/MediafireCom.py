# -*- coding: utf-8 -*-

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.captcha.SolveMedia import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster


class MediafireCom(SimpleHoster):
    __name__    = "MediafireCom"
    __type__    = "hoster"
    __version__ = "0.95"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?mediafire\.com/(file/|view/\??|download(\.php\?|/)|\?)(?P<ID>\w+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

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
        self.multiDL         = True


    def handle_captcha(self):
        solvemedia  = SolveMedia(self.pyfile)
        captcha_key = solvemedia.detect_key()

        if captcha_key:
            self.captcha = solvemedia
            response, challenge = solvemedia.challenge(captcha_key)
            self.data = self.load("http://www.mediafire.com/?" + self.info['pattern']['ID'],
                                  post={'adcopy_challenge': challenge,
                                        'adcopy_response' : response})
            return

        recaptcha   = ReCaptcha(self.pyfile)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            url, inputs = self.parse_html_form('name="form_captcha"')
            self.log_debug(("form_captcha url:%s inputs:%s") % (url, inputs))

            if url:
                self.captcha = recaptcha
                response, challenge = recaptcha.challenge(captcha_key)

                inputs['g-recaptcha-response'] = response
                self.data = self.load(self.fixurl(url), post=inputs)

            else:
                self.fail("ReCaptcha form not found")


    def handle_free(self, pyfile):
        self.handle_captcha()

        if self.PASSWORD_PATTERN in self.data:
            password = self.get_password()

            if not password:
                self.fail(_("No password found"))
            else:
                self.log_info(_("Password protected link, trying: ") + password)
                self.data = self.load(self.link, post={'downloadp': password})

                if self.PASSWORD_PATTERN in self.data:
                    self.fail(_("Wrong password"))

        return super(MediafireCom, self).handle_free(pyfile)
