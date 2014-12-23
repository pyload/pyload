# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class CloudzillaTo(SimpleHoster):
    __name__    = "CloudzillaTo"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/file/(?P<ID>[\w^_]+)'

    __description__ = """Cloudzilla.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'title="(?P<N>.+?)">\1</span> <span class="size">\((?P<S>[\d.]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File not found...<'


    def handleFree(self):
        self.html = self.load("http://www.cloudzilla.to/generateticket/",
                              post={'file_id': self.info['pattern']['ID'], 'key': self.getPassword()})

        ticket = dict(re.findall(r'<(.+?)>([^<>]+?)</', self.html))

        self.logDebug(ticket)

        if 'error' in ticket:
            self.fail(ticket['error'])

        if 'wait' in ticket:
            self.wait(int(ticket['wait']), int(ticket['wait']) > 5)

        self.link = "http://%(server)s/download/%(file_id)s/%(ticket_id)s" % {'server'   : ticket['server'],
                                                                              'file_id'  : self.info['pattern']['ID'],
                                                                              'ticket_id': ticket['ticket_id']})


    def handlePremium(self):
        return self.handleFree()


getInfo = create_getInfo(CloudzillaTo)
