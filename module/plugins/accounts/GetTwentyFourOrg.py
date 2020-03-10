# -*- coding: utf-8 -*-

import time
import pycurl
from hashlib import sha256

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


class GetTwentyFourOrg(MultiAccount):
    __name__ = 'GetTwentyFourOrg'
    __type__ = 'account'
    __version__ = '0.03'
    __status__ = 'testing'

    __description__ = 'GeT24.org account plugin'
    __license__ = 'GPLv3'
    __authors__ = ['get24', 'contact@get24.org']

    API_URL = 'https://get24.org/api'

    def grab_hosters(self, user, password, data):
        rc = self.load('%s/hosts/enabled' % self.API_URL)
        hosts = json.loads(rc)
        self.log_debug(hosts)
        return hosts

    def grab_info(self, user, password, data):
        post = {'email': user,
                'passwd_sha256': self.info['data']['passwd_sha256']}
        rc = self.load('%s/login' % self.API_URL, post=post)
        rc = json.loads(rc)
        self.log_debug(rc)

        validuntil = time.mktime(time.strptime(rc['date_expire'], '%Y-%m-%d'))

        return {'validuntil': validuntil,
                'trafficleft': rc['transfer_left'],
                'premium': rc['status'] == 'premium'}

    def signin(self, user, password, data):
        data['passwd_sha256'] = sha256(password.encode('ascii')).hexdigest()
        self.req.http.c.setopt(
            pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version).encode()
        )
