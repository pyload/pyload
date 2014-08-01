# -*- coding: utf-8 -*-

import re

from hashlib import md5

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.hoster.XFileSharingPro import XFileSharingPro


def getInfo(urls):
    # DDLStorage API Documentation:
    # http://www.ddlstorage.com/cgi-bin/api_req.cgi?req_type=doc
    ids = dict()
    for url in urls:
        m = re.search(DdlstorageCom.__pattern__, url)
        ids[m.group('ID')] = url

    for chunk in chunks(ids.keys(), 5):
        for _ in xrange(5):
            api = getURL('http://www.ddlstorage.com/cgi-bin/api_req.cgi',
                         post={'req_type': 'file_info_free',
                               'client_id': 53472,
                               'file_code': ','.join(chunk),
                               'sign': md5('file_info_free%d%s%s' % (53472, ','.join(chunk),
                                                                     '25JcpU2dPOKg8E2OEoRqMSRu068r0Cv3')).hexdigest()})
            api = api.replace('<pre>', '').replace('</pre>', '')
            api = json_loads(api)
            if 'error' not in api:
                break

        result = list()
        for el in api:
            if el['status'] == 'online':
                result.append((el['file_name'], int(el['file_size']), 2, ids[el['file_code']]))
            else:
                result.append((ids[el['file_code']], 0, 1, ids[el['file_code']]))
        yield result


class DdlstorageCom(XFileSharingPro):
    __name__ = "DdlstorageCom"
    __type__ = "hoster"
    __version__ = "1.01"

    __pattern__ = r'http://(?:www\.)?ddlstorage.com/(?P<ID>\w{12})'

    __description__ = """DDLStorage.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    HOSTER_NAME = "ddlstorage.com"

    FILE_INFO_PATTERN = r'<p class="sub_title"[^>]*>(?P<N>.+) \((?P<S>[^)]+)\)</p>'


    def prepare(self):
        self.getAPIData()
        super(DdlstorageCom, self).prepare()

    def getAPIData(self):
        file_id = re.match(self.__pattern__, self.pyfile.url).group('ID')
        data = {'client_id': 53472,
                'file_code': file_id}
        if self.user:
            passwd = self.account.getAccountData(self.user)['password']
            data['req_type'] = 'file_info_reg'
            data['user_login'] = self.user
            data['user_password'] = md5(passwd).hexdigest()
            data['sign'] = md5('file_info_reg%d%s%s%s%s' % (data['client_id'], data['user_login'],
                                                            data['user_password'], data['file_code'],
                                                            '25JcpU2dPOKg8E2OEoRqMSRu068r0Cv3')).hexdigest()
        else:
            data['req_type'] = 'file_info_free'
            data['sign'] = md5('file_info_free%d%s%s' % (data['client_id'], data['file_code'],
                                                         '25JcpU2dPOKg8E2OEoRqMSRu068r0Cv3')).hexdigest()

        self.api_data = self.load('http://www.ddlstorage.com/cgi-bin/api_req.cgi', post=data)
        self.api_data = self.api_data.replace('<pre>', '').replace('</pre>', '')
        self.logDebug('API Data: ' + self.api_data)
        self.api_data = json_loads(self.api_data)[0]

        if self.api_data['status'] == 'offline':
            self.offline()

        if 'file_name' in self.api_data:
            self.pyfile.name = self.api_data['file_name']
        if 'file_size' in self.api_data:
            self.pyfile.size = self.api_data['size'] = self.api_data['file_size']
        if 'file_md5_base64' in self.api_data:
            self.api_data['md5_ddlstorage'] = self.api_data['file_md5_base64']
