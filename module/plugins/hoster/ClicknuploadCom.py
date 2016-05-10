# -*- coding: utf-8 -*-

import  re

from module.plugins.internal.SimpleHoster import SimpleHoster


class ClicknuploadCom(SimpleHoster):
    __name__    = "ClicknuploadCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?clicknupload\.(?:com|me|link)/\w{12}'
    __config__ = [("activated"   , "bool", "Activated"                                        , True),
                  ("use_premium" , "bool", "Use premium account if available"                 , True),
                  ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                  ("chk_filesize", "bool", "Check file size"                                  , True),
                  ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Clicknupload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tbsn"     , "tbsnpy_github@gmx.de"      ),
                       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'<b>Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    LINK_PATTERN = r'onClick="window.open\(\'(.+?)\'\);"'

    OFFLINE_PATTERN = r'<b>File Not Found</b>'

    WAIT_PATTERN = r'>Please wait <.+?>(\d+)<'

    URL_REPLACEMENTS = [(r'clicknupload\.(?:me|com)', "clicknupload.link")]


    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form("action=''")
        if not inputs:
            self.fail(_("Form 1 not found"))

        self.data = self.load(pyfile.url, post=inputs)

        self.check_errors()

        action, inputs = self.parse_html_form('name="F1"')
        if not inputs:
            self.fail(_("Form 2 not found"))

        self.data = self.load(pyfile.url, post=inputs)

        m = re.search(self.LINK_PATTERN, self.data)
        if m:
            self.link = m.group(1)
