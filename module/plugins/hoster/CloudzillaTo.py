# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class CloudzillaTo(SimpleHoster):
    __name__    = "CloudzillaTo"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/file/(?P<ID>[\w^_]+)'

    __description__ = """Cloudzilla.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'title="(?P<N>.+?)">\1</span> <span class="size">\((?P<S>[\d.]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File not found...<'

    PASSWORD_PATTERN = r'<div id="pwd_protected">'


    def checkErrors(self):
        m = re.search(self.PASSWORD_PATTERN, self.html)
        if m:
            self.html = self.load(self.pyfile.url, get={'key': self.getPassword()})

        if re.search(self.PASSWORD_PATTERN, self.html):
            self.retry(reason="Wrong password")


    def handleFree(self):
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
            self.wait(int(ticket['wait']), int(ticket['wait']) > 5)

        self.link = "http://%(server)s/download/%(file_id)s/%(ticket_id)s" % {'server'   : ticket['server'],
                                                                              'file_id'  : self.info['pattern']['ID'],
                                                                              'ticket_id': ticket['ticket_id']}


    def handlePremium(self):
        return self.handleFree()


getInfo = create_getInfo(CloudzillaTo)
