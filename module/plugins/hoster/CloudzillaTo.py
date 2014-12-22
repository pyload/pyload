# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads


class CloudzillaTo(SimpleHoster):
    __name__    = "CloudzillaTo"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/file/(?P<ID>[\w^_]+)'

    __description__ = """Cloudzilla.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'>(?P<N>.+?)</span> <span class="size">\((?P<S>[\d.]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File not found...<'


    def handleFree(self):
        ticket = json_loads(self.load("http://www.cloudzilla.to/generateticket/",
                                      post={'file_id': self.info['pattern']['ID'], 'key': ""}))['result']

        if ticket['status'] is "error":
            self.fail(ticket['status']['error'])

        if 'wait' in ticket:
            wait_time = int(ticket['wait'])
            self.wait(wait_time, wait_time > 5)

        self.download("http://%(server)s/download/%(file_id)s/%(ticket_id)s" % {'server'   : ticket['server'],
                                                                                'file_id'  : self.info['pattern']['ID'],
                                                                                'ticket_id': ticket['ticket_id']})


    def handlePremium(self):
        return self.handleFree()


getInfo = create_getInfo(CloudzillaTo)
