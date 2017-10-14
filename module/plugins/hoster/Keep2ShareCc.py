# -*- coding: utf-8 -*-

import re

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import json


class Keep2ShareCc(SimpleHoster):
    __name__ = "Keep2ShareCc"
    __type__ = "hoster"
    __version__ = "0.43"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Keep2Share.cc hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    DISPOSITION = False  # @TODO: Recheck in v0.4.10

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://k2s.cc/file/\g<ID>")]

    API_URL = "https://keep2share.cc/api/v2/"
    #: See https://github.com/keep2share/api

    @classmethod
    def api_response(cls, method, **kwargs):
        html = get_url(cls.API_URL + method,
                       post=json.dumps(kwargs))
        return json.loads(html)

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group('ID')
        file_info = cls.api_response("GetFilesInfo", ids=[file_id], extended_info=False)

        if file_info['code'] != 200 or \
                        len(file_info['files']) == 0 or \
                        file_info['files'][0].get("is_available", False) is False:
            return {'status': 1}

        else:
            return {'name': file_info['files'][0]['name'],
                    'size': file_info['files'][0]['size'],
                    'md5': file_info['files'][0]['md5'],
                    'access': file_info['files'][0]['access'],
                    'status': 2 if file_info['files'][0]['is_available'] else 1}

    def setup(self):
        self.multiDL = self.premium
        self.resume_download = True

    def handle_free(self, pyfile):
        file_id = self.info['pattern']['ID']

        if self.info['access'] == "premium":
            self.fail(_("File can be downloaded by premium users only"))

        elif self.info['access'] == "private":
            self.fail(_("This is a private file"))

        try:
            json_data = self.api_response("GetUrl",
                                          file_id=file_id,
                                          free_download_key=None,
                                          captcha_challenge=None,
                                          captcha_response=None)
        except BadHeader, e:
            if e.code == 406:
                for i in range(10):
                    json_data = self.api_response("RequestCaptcha")
                    if json_data['code'] != 200:
                        self.fail(_("Request captcha API failed"))

                    captcha_response = self.captcha.decrypt(json_data['captcha_url'])
                    try:
                        json_data = self.api_response("GetUrl",
                                                      file_id=file_id,
                                                      free_download_key=None,
                                                      captcha_challenge=json_data['challenge'],
                                                      captcha_response=captcha_response)

                    except BadHeader, e:
                        if e.code == 406:
                            json_data = json.loads(e.content)
                            if json_data['errorCode'] == 31:  #: ERROR_CAPTCHA_INVALID
                                self.captcha.invalid()
                                continue

                            elif json_data['errorCode'] == 42:  #: ERROR_DOWNLOAD_NOT_AVAILABLE
                                self.captcha.correct()
                                self.retry(wait=json_data['errors'][0]['timeRemaining'])

                            else:
                                self.fail(json_data['message'])

                        else:
                            raise

                    else:
                        self.captcha.correct()
                        free_download_key = json_data['free_download_key']
                        break

                else:
                    self.fail(_("Max captcha retries reached"))

                self.wait(json_data['time_wait'])

                json_data = self.api_response("GetUrl",
                                              file_id=file_id,
                                              free_download_key=free_download_key,
                                              captcha_challenge=None,
                                              captcha_response=None)

                if json_data['code'] == 200:
                    self.link = json_data['url']

            else:
                raise

        else:
            self.link = json_data['url']

    def handle_premium(self, pyfile):
        file_id = self.info['pattern']['ID']

        if self.info['access'] == "private":
            self.fail(_("This is a private file"))

        json_data = self.api_response("GetUrl",
                                      file_id=file_id,
                                      free_download_key=None,
                                      captcha_challenge=None,
                                      captcha_response=None,
                                      auth_token=self.account.info['data']['token'])

        self.link = json_data['url']
