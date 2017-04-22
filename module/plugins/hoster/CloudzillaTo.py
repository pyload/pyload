# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class CloudzillaTo(SimpleHoster):
    __name__ = "CloudzillaTo"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/file/(?P<ID>[\w^_]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cloudzilla.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    INFO_PATTERN = r'title="(?P<N>.+?)">\1</span> <span class="size">\((?P<S>[\d.]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File not found...<'

    PASSWORD_PATTERN = r'<div id="pwd_protected">'

    def check_errors(self):
        if re.search(self.PASSWORD_PATTERN, self.data):
            pw = self.get_password()
            if pw:
                self.data = self.load(self.pyfile.url, get={'key': pw})
            else:
                self.fail(_("Missing password"))

        if re.search(self.PASSWORD_PATTERN, self.data):
            self.retry(msg="Wrong password")
        else:
            return SimpleHoster.check_errors(self)

    def handle_free(self, pyfile):
        self.data = self.load("http://www.cloudzilla.to/generateticket/",
                              post={'file_id': self.info['pattern']['ID'], 'key': self.get_password()})

        ticket = dict(re.findall(r'<(.+?)>([^<>]+?)</', self.data))

        self.log_debug(ticket)

        if 'error' in ticket:
            if "File is password protected" in ticket['error']:
                self.retry(msg="Wrong password")
            else:
                self.fail(ticket['error'])

        if 'wait' in ticket:
            self.wait(ticket['wait'], int(ticket['wait']) > 5)

        self.link = "http://%(server)s/download/%(file_id)s/%(ticket_id)s" % {'server': ticket['server'],
                                                                              'file_id': self.info['pattern']['ID'],
                                                                              'ticket_id': ticket['ticket_id']}

    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)
