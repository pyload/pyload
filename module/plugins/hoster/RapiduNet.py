# -*- coding: utf-8 -*-

import re
import time

import pycurl

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json, seconds_to_midnight
from ..internal.SimpleHoster import SimpleHoster


class RapiduNet(SimpleHoster):
    __name__ = "RapiduNet"
    __type__ = "hoster"
    __version__ = "0.20"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?rapidu\.net/(?P<ID>\d+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Rapidu.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    COOKIES = [("rapidu.net", "rapidu_lang", "en")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://rapidu.net/\g<ID>")]

    RECAPTCHA_KEY = r'6LcOuQkUAAAAAF8FPp423qz-U2AXon68gJSdI_W4'

    # https://rapidu.net/documentation/api/
    API_URL = 'https://rapidu.net/api/'

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method + "/", post=kwargs)
        return json.loads(json_data)

    def api_info(self, url):
        file_id = re.match(self.__pattern__, url).group('ID')
        api_data = self.api_request("getFileDetails", id=file_id)['0']

        if api_data['fileStatus'] == 1:
            return {'status': 2,
                    'name': api_data['fileName'],
                    'size': int(api_data['fileSize'])}
        else:
            return {'status': 1}

    def setup(self):
        self.resume_download = True
        self.multiDL = self.premium

    def handle_free(self, pyfile):
        self.req.http.lastURL = pyfile.url
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        json_data = self.get_json_response("https://rapidu.net/ajax.php",
                                           get={'a': "getLoadTimeToDownload"},
                                           post={'_go': ""})

        if str(json_data['timeToDownload']) == "stop":
            self.log_warning(_("You've reach your daily download transfer"))
            self.retry(10, wait=seconds_to_midnight(), msg=_("You've reach your daily download transfer"))

        self.set_wait(int(json_data['timeToDownload']) - int(time.time()))

        self.captcha = ReCaptcha(pyfile)
        response = self.captcha.challenge(self.RECAPTCHA_KEY)

        self.wait()

        json_data = self.get_json_response("https://rapidu.net/ajax.php",
                                           get={'a': "getCheckCaptcha"},
                                           post={'_go': "",
                                                 'captcha1': response,
                                                 'fileId': self.info['pattern']['ID']})

        if json_data['message'] == "success":
            self.link = json_data['url']

    def handle_premium(self, pyfile):
        api_data = self.api_request("getFileDownload",
                                    id=self.info['pattern']['ID'],
                                    login=self.account.user,
                                    password=self.account.info['login']['password'])

        if "message" in api_data:
            self.fail(api_data['message']['error'])
        else:
            self.link = api_data.get("fileLocation")

    def get_json_response(self, *args, **kwargs):
        res = self.load(*args, **kwargs)
        if not res.startswith('{'):
            self.retry()

        self.log_debug(res)

        return json.loads(res)
