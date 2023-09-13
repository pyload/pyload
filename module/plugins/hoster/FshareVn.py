# -*- coding: utf-8 -*-

import re
import urlparse

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.misc import BIGHTTPRequest, json
from ..internal.SimpleHoster import SimpleHoster


class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __version__ = "0.41"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fshare\.vn/file/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """FshareVn hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = ur'Tập tin của bạn yêu cầu không tồn tại'
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    URL_REPLACEMENTS = [("http://", "https://")]

    API_KEY = "dMnqMMZMUnN5YpvKENaEhdQQ5jxDqddt"
    API_USERAGENT = "pyLoad-B1RS5N"
    API_URL = "https://api.fshare.vn/api/"

    # See https://www.fshare.vn/api-doc
    def api_request(self, method, session_id=None, **kwargs):
        self.req.http.c.setopt(pycurl.USERAGENT, self.API_USERAGENT)

        if len(kwargs) == 0:
            json_data = self.load(self.API_URL + method,
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        else:
            self.req.http.c.setopt(pycurl.HTTPHEADER, ["Content-Type: application/json"])
            json_data = self.load(self.API_URL + method,
                                  post=json.dumps(kwargs),
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        return json.loads(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group('ID')

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["Accept: application/json, text/plain, */*"])
        file_info = json.loads(self.load("https://www.fshare.vn/api/v3/files/folder",
                                         get={'linkcode': file_id}))

        if file_info.get("status") == 404:
            info['status'] = 1

        else:
            info.update({'name': file_info['current']['name'],
                         'size': file_info['current']['size'],
                         'status': 2})

        return info

    def setup(self):
        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.requestFactory.getOptions(),
            limit=5000000)

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('class="password-form"')
        if action is not None:
            password = self.get_password()
            if password:
                inputs['DownloadPasswordForm[password]'] = password

            else:
                self.fail(_("Download is password protected"))

            url = urlparse.urljoin(pyfile.url, action)

            self.data = self.load(url, post=inputs)
            if ur'Sai mật khẩu' in self.data:
                self.fail(_("Wrong password"))

        action, inputs = self.parse_html_form('id="form-download"', input_names={'withFcode5': "0"})
        url = urlparse.urljoin(pyfile.url, action)

        if not inputs:
            self.error(_("Free Download form not found"))

        self.data = self.load(url, post=inputs)

        try:
            json_data = json.loads(self.data)

        except ValueError:
            self.fail(_("Expected JSON data"))

        err_msg = json_data.get('msg')
        if err_msg:
            self.fail(err_msg)

        elif json_data.get('policydowload', False):
            self.fail(_("File can be downloaded by premium users only"))

        elif 'url' not in json_data:
            self.fail(_("Unexpected response"))

        wait_time = json_data.get('wait_time', None)
        wait_time = 35 if wait_time is None else int(wait_time)
        self.wait(wait_time)

        self.link = json_data['url']

    def handle_premium(self, pyfile):
        try:
            password = self.get_password()
            if password:
                api_data = self.api_request("session/download",
                                            session_id=self.account.info['data']['session_id'],
                                            token=self.account.info['data']['token'],
                                            url=pyfile.url,
                                            password=password)

            else:
                api_data = self.api_request("session/download",
                                            session_id=self.account.info['data']['session_id'],
                                            token=self.account.info['data']['token'],
                                            url=pyfile.url)

        except BadHeader, e:
                if e.code == 403:
                    if password:
                        self.fail(_("Wrong password"))

                    else:
                        self.fail(_("Download is password protected"))

                elif e.code != 200:
                    self.log_debug("Download failed, error code %s" % e.code)
                    self.offline()

        self.link = api_data['location']
