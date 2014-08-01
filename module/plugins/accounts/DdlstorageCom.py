# -*- coding: utf-8 -*-

from hashlib import md5
from time import mktime, strptime

from module.plugins.internal.XFSPAccount import XFSPAccount
from module.common.json_layer import json_loads
from module.utils import parseFileSize

# DDLStorage API Documentation:
# http://www.ddlstorage.com/cgi-bin/api_req.cgi?req_type=doc


class DdlstorageCom(XFSPAccount):
    __name__ = "DdlstorageCom"
    __type__ = "account"
    __version__ = "1.00"

    __description__ = """DDLStorage.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    MAIN_PAGE = "http://ddlstorage.com/"


    def loadAccountInfo(self, user, req):
        password = self.accounts[user]['password']
        api_data = req.load('http://www.ddlstorage.com/cgi-bin/api_req.cgi',
                            post={'req_type': 'user_info',
                                  'client_id': 53472,
                                  'user_login': user,
                                  'user_password': md5(password).hexdigest(),
                                  'sign': md5('user_info%d%s%s%s' % (53472, user, md5(password).hexdigest(),
                                                                     '25JcpU2dPOKg8E2OEoRqMSRu068r0Cv3')).hexdigest()})
        api_data = api_data.replace('<pre>', '').replace('</pre>', '')
        self.logDebug('Account Info API data: ' + api_data)
        api_data = json_loads(api_data)

        if api_data['status'] != 'OK':  # 'status' must be always OK for a working account
            return {"premium": False, "valid": False}

        if api_data['account_type'] == 'REGISTERED':
            premium = False
            validuntil = None
        else:
            premium = True
            validuntil = int(mktime(strptime(api_data['premium_expire'], "%Y-%m-%d %H:%M:%S")))

        if api_data['usr_bandwidth_available'] == 'UNLIMITED':
            trafficleft = -1
        else:
            trafficleft = parseFileSize(api_data['usr_bandwidth_available']) / 1024

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}
