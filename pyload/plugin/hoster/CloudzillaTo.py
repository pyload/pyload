# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class CloudzillaTo(SimpleHoster):
    __name    = "CloudzillaTo"
    __type    = "hoster"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?cloudzilla\.to/share/file/(?P<ID>[\w^_]+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Cloudzilla.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'title="(?P<N>.+?)">\1</span> <span class="size">\((?P<S>[\d.]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File not found...<'

    PASSWORD_PATTERN = r'<div id="pwd_protected">'


    def checkErrors(self):
        m = re.search(self.PASSWORD_PATTERN, self.html)
        if m:
            self.html = self.load(self.pyfile.url, get={'key': self.getPassword()})

        if re.search(self.PASSWORD_PATTERN, self.html):
            self.retry(reason="Wrong password")


    def handle_free(self, pyfile):
        self.html = self.load("http://www.cloudzilla.to/generateticket/",
                              post={'file_id': self.info['pattern']['ID'], 'key': self.getPassword()})

        ticket = dict(re.findall(r'<(.+?)>([^<>]+?)</', self.html))

        self.logDebug(ticket)

        if 'error' in ticket:
            if "File is password protected" in ticket['error']:
                self.retry(reason="Wrong password")
            else:
                self.fail(ticket['error'])

        if 'wait' in ticket:
            self.wait(ticket['wait'], int(ticket['wait']) > 5)

        self.link = "http://%(server)s/download/%(file_id)s/%(ticket_id)s" % {'server'   : ticket['server'],
                                                                              'file_id'  : self.info['pattern']['ID'],
                                                                              'ticket_id': ticket['ticket_id']}


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)
