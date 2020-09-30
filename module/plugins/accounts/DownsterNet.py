# -*- coding: utf-8 -*-

import pycurl, random, string
from time import time, mktime
from datetime import datetime

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount
from ...network.HTTPRequest import BadHeader


class DownsterNet(MultiAccount):
    __name__ = "DownsterNet"
    __type__ = "account"
    __version__ = "0.2"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12)
    ]

    __description__ = """Downster.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    API_URL = "https://downster.net/api"

    def rnd(self):
        return ''.join([random.choice(string.ascii_lowercase + string.digits) for n in xrange(5)])

    def flow_id(self):
        self.log_debug('User flow id: %s' % self.info['data'].get('user_flow_id'))
        if not self.info['data'].get('user_flow_id'):
            self.info['data']['user_flow_id'] = self.rnd()
            self.log_info('Created user flow id: %s' % self.info['data'].get('user_flow_id'))

        return 'PYL_' + self.info['data']['user_flow_id'] + '_' + self.rnd()

    # Overwrite this function to prevent cleanCookies to don't remove token cookie
    def clean(self):
        try:
            self.req.close()
        except Exception:
            pass

    def api_request(self, method, get={}, post={}):
        # This will create a new request object for every request. Passing the user will add the cookiejar for
        # the wanted account. A new request object is necessary as setting headers for a new request
        # while a download still uses self.req throws an error
        req = self.pyload.requestFactory.getRequest(self.classname, self.user)
        req.setOption("timeout", 60)  # @TODO: Remove in 0.4.10
        req.http.c.setopt(pycurl.HTTPHEADER, [
            "Accept: application/json, text/plain, */",
            "Content-Type: application/json",
            "X-Flow-ID: " + self.flow_id(),
            "User-Agent: PYLoad/" + self.pyload.version + " DownsterNet/" + self.__version__
        ])

        try:
            return json.loads(self.load(self.API_URL + method, get=get, post=json.dumps(post), req=req))
        except BadHeader as e:
            self.log_debug("Request failed:  " + str(e.code), e)
            return json.loads(e.content)

    def grab_hosters(self, user, password, data):
        return self.get_data('hosters')

    # Will be automatically called after 30 minutes timeout
    def signin(self, email, password, data):
        # Get user info if still logged in (no cookies cleared)
        payload = self.api_request('/user/info')
        # Login if token in cookies is outdated
        if not payload['success']:
            payload = self.api_request('/user/authenticate', post={'email': email, 'password': password})

        if not payload['success']:
            self.fail_login(payload['error'])
            return

        # Parse rfc3339 time format
        date = datetime.strptime(payload['data']['premiumUntil'], '%Y-%m-%dT%H:%M:%S.%f+00:00')
        self.log_debug(date)
        #: Parse account info
        self.info['validuntil'] = mktime(date.timetuple())
        self.info['trafficleft'] = -1
        self.info['data']['premium'] = self.info['validuntil'] > time()

        usage = self.api_request('/download/usage')
        if not usage['success']:
            self.fail_login(usage['error'])
            return

        self.info['data']['hosters'] = [hoster['hoster'] for hoster in usage['data']]
        self.log_info("Logged in")
