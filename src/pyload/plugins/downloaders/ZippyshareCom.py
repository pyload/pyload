# -*- coding: utf-8 -*-

import re
import urllib.parse

from bs4 import BeautifulSoup

from pyload.core.utils.misc import eval_js

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class ZippyshareCom(SimpleDownloader):
    __name__ = "ZippyshareCom"
    __type__ = "downloader"
    __version__ = "0.98"
    __status__ = "testing"

    __pattern__ = r"https?://(?P<HOST>www\d{0,3}\.zippyshare\.com)/(?:[vd]/|view\.jsp.*key=)(?P<KEY>[\w^_]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Zippyshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("sebdelsol", "seb.morin@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    COOKIES = [("zippyshare.com", "ziplocale", "en")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://\g<HOST>/v/\g<KEY>/file.html")]

    NAME_PATTERN = r'(?:<title>Zippyshare.com - |"/)(?P<N>[^/]+)(?:</title>|";)'
    SIZE_PATTERN = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r"does not exist (anymore )?on this server<"
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    LINK_PATTERN = r"document.location = '(.+?)'"

    def setup(self):
        self.chunk_limit = -1
        self.multi_dl = True
        self.resume_download = True

    def handle_free(self, pyfile):
        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            try:
                self.link = re.search(self.LINK_PATTERN, self.data)
                self.captcha.challenge()

            except Exception as exc:
                self.error(exc)

        else:
            self.link = self.fixurl(self.get_link())
            if ".com/pd/" in self.link:
                self.load(self.link)
                self.link = self.link.replace(".com/pd/", ".com/d/")

        if self.link and pyfile.name == "file.html":
            pyfile.name = urllib.parse.unquote(self.link.split("/")[-1])

    def get_link(self):
        #: Get all the scripts inside the html body
        soup = BeautifulSoup(self.data)
        scripts = [
            s.getText()
            for s in soup.body.findAll("script", type="text/javascript")
            if "('dlbutton').href =" in s.getText()
        ]

        #: Emulate a document in JS
        inits = [
            """
                var document = {}
                document.getElementById = function(x) {
                    if (!this.hasOwnProperty(x)) {
                        this[x] = {getAttribute : function(x) { return this[x] } }
                    }
                    return this[x]
                }
                """
        ]

        #: inits is meant to be populated with the initialization of all the DOM elements found in the scripts
        eltRE = r'getElementById\([\'"](.+?)[\'"]\)(\.)?(getAttribute\([\'"])?(\w+)?([\'"]\))?'
        for m in re.findall(eltRE, " ".join(scripts)):
            JSid, JSattr = m[0], m[3]
            values = [
                f for f in (elt.get(JSattr, None) for elt in soup.findAll(id=JSid)) if f
            ]
            if values:
                inits.append(
                    'document.getElementById("{}")["{}"] = "{}"'.format(
                        JSid, JSattr, values[-1]
                    )
                )

        #: Add try/catch in JS to handle deliberate errors
        scripts = ["\n".join(("try{", script, "} catch(err){}")) for script in scripts]

        #: Get the file's url by evaluating all the scripts
        scripts = inits + scripts + ["document.dlbutton.href"]

        return eval_js("\n".join(scripts))
