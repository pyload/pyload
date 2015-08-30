# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__    = "OneFichierCom"
    __type__    = "hoster"
    __version__ = "0.90"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:(?P<ID1>\w+)\.)?(?P<HOST>1fichier\.com|alterupload\.com|cjoint\.net|d(es)?fichiers\.com|dl4free\.com|megadl\.fr|mesfichiers\.org|piecejointe\.net|pjointe\.com|tenvoi\.com)(?:/\?(?P<ID2>\w+))?'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """1fichier.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("the-razer", "daniel_ AT gmx DOT net"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("imclem", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Ludovic Lehmann", "ludo.lehmann@gmail.com")]


    COOKIES     = [("1fichier.com", "LG", "en")]

    DIRECT_LINK = True

    NAME_PATTERN    = r'>File\s*Name :</td>\s*<td.*>(?P<N>.+?)<'
    SIZE_PATTERN    = r'>Size :</td>\s*<td.*>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'File not found !\s*<'

    WAIT_PATTERN = r'>You must wait \d+ minutes'


    def setup(self):
        self.multiDL        = self.premium
        self.resume_download = True


    @classmethod
    def get_info(cls, url="", html=""):
        redirect = url
        for i in xrange(10):
            try:
                headers = dict(re.findall(r"(?P<name>.+?): (?P<value>.+?)\r?\n", get_url(redirect, just_header=True).lower()))
                if 'location' in headers and headers['location']:
                    redirect = headers['location']
                else:
                    if 'content-type' in headers and headers['content-type'] == "application/octet-stream":
                        if "filename=" in headers.get('content-disposition'):
                            name = dict(_i.split("=") for _i in map(str.strip, headers['content-disposition'].split(";"))[1:])['filename'].strip("\"'")
                        else:
                            name = url

                        info = {'name'  : name,
                                'size'  : long(headers.get('content-length')),
                                'status': 3,
                                'url'   : url}

                    else:
                        info = super(OneFichierCom, cls).get_info(url, html)

                    break

            except Exception, e:
                info = {'status' : 8,
                        'error'  : e.message}

        else:
            info = {'status' : 8,
                    'error'    : _("Too many redirects")}

        return info


    def handle_direct(self, pyfile):
        redirect = pyfile.url
        for i in xrange(self.get_config("maxredirs", plugin="UserAgentSwitcher")):

            headers = self.load(redirect, just_header=True)
            if 'location' in headers and headers['location']:
                self.log_debug("Redirect #%d to: %s" % (i, redirect))
                redirect = headers['location']
            else:
                if 'content-type' in headers and headers['content-type'] == "application/octet-stream":
                    self.link = pyfile.url
                break
        else:
            self.fail(_("Too many redirects"))


    def handle_free(self, pyfile):
        self.check_errors()

        id = self.info['pattern']['ID1'] or self.info['pattern']['ID2']
        url, inputs = self.parse_html_form('action="https://1fichier.com/\?%s' % id)

        if not url:
            self.fail(_("Download link not found"))

        if "pass" in inputs:
            inputs['pass'] = self.get_password()

        inputs['submit'] = "Download"

        self.download(url, post=inputs)


    def handle_premium(self, pyfile):
        self.download(pyfile.url, post={'dl': "Download", 'did': 0})


getInfo = create_getInfo(OneFichierCom)
