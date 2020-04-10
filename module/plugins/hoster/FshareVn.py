# -*- coding: utf-8 -*-

import re
import urlparse

import pycurl
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest as get_request

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __version__ = "0.33"
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

    URL_REPLACEMENTS = [("http://", "https://")]

    API_KEY = "L2S7R6ZMagggC5wWkQhX2+aDi467PPuftWUMRFSn"
    API_URL = "https://api.fshare.vn/api/"

    def api_response(self, method, session_id=None, **kwargs):
        self.req.http.c.setopt(pycurl.USERAGENT, "okhttp/3.6.0")

        if len(kwargs) == 0:
            json_data = self.load(self.API_URL + method,
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        else:
            json_data = self.load(self.API_URL + method,
                                  post=json.dumps(kwargs),
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        return json.loads(json_data)

    @classmethod
    def api_info(cls, url):
        info = {}
        file_id = re.match(cls.__pattern__, url).group('ID')
        req = get_request()

        req.c.setopt(pycurl.HTTPHEADER, ["Accept: application/json, text/plain, */*"])
        file_info = json.loads(req.load("https://www.fshare.vn/api/v3/files/folder",
                                        get={'linkcode': file_id}))

        req.close()

        if file_info.get("status") == 404:
            info['status'] = 1

        else:
            info.update({'name': file_info['current']['name'],
                         'size': file_info['current']['size'],
                         'status': 2})

        return info

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

        except Exception:
            self.fail(_("Expected JSON data"))

        err_msg = json_data.get('msg')
        if err_msg:
            self.fail(err_msg)

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
                api_data = self.api_response("session/download",
                                             token=self.account.info['data']['token'],
                                             url=pyfile.url,
                                             password=password)

            else:
                api_data = self.api_response("session/download",
                                             token=self.account.info['data']['token'],
                                             url=pyfile.url)

        except BadHeader, e:
                if e.code == 403:
                    if password:
                        self.fail(_("Wrong password"))

                    else:
                        self.fail(_("Download is password protected"))

                elif e.code != 200:
                    self.offline()

        self.link = api_data['location']
