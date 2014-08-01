# -*- coding: utf-8 -*-

import re

from time import time

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilepostCom(SimpleHoster):
    __name__ = "FilepostCom"
    __type__ = "hoster"
    __version__ = "0.28"

    __pattern__ = r'https?://(?:www\.)?(?:filepost\.com/files|fp.io)/([^/]+).*'

    __description__ = """Filepost.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_INFO_PATTERN = r'<input type="text" id="url" value=\'<a href[^>]*>(?P<N>[^>]+?) - (?P<S>[0-9\.]+ [kKMG]i?B)</a>\' class="inp_text"/>'
    OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>|<div class="file_info file_info_deleted">'

    PREMIUM_ONLY_PATTERN = r'members only. Please upgrade to premium|a premium membership is required to download this file'
    RECAPTCHA_KEY_PATTERN = r"Captcha.init\({\s*key:\s*'([^']+)'"
    FLP_TOKEN_PATTERN = r"set_store_options\({token: '([^']+)'"


    def handleFree(self):
        # Find token and captcha key
        file_id = re.match(self.__pattern__, self.pyfile.url).group(1)

        m = re.search(self.FLP_TOKEN_PATTERN, self.html)
        if m is None:
            self.parseError("Token")
        flp_token = m.group(1)

        m = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
        if m is None:
            self.parseError("Captcha key")
        captcha_key = m.group(1)

        # Get wait time
        get_dict = {'SID': self.req.cj.getCookie('SID'), 'JsHttpRequest': str(int(time() * 10000)) + '-xml'}
        post_dict = {'action': 'set_download', 'token': flp_token, 'code': file_id}
        wait_time = int(self.getJsonResponse(get_dict, post_dict, 'wait_time'))

        if wait_time > 0:
            self.wait(wait_time)

        post_dict = {"token": flp_token, "code": file_id, "file_pass": ''}

        if 'var is_pass_exists = true;' in self.html:
            # Solve password
            for file_pass in self.getPassword().splitlines():
                get_dict['JsHttpRequest'] = str(int(time() * 10000)) + '-xml'
                post_dict['file_pass'] = file_pass
                self.logInfo("Password protected link, trying " + file_pass)

                download_url = self.getJsonResponse(get_dict, post_dict, 'link')
                if download_url:
                    break

            else:
                self.fail("No or incorrect password")

        else:
            # Solve recaptcha
            recaptcha = ReCaptcha(self)

            for i in xrange(5):
                get_dict['JsHttpRequest'] = str(int(time() * 10000)) + '-xml'
                if i:
                    post_dict['recaptcha_challenge_field'], post_dict['recaptcha_response_field'] = recaptcha.challenge(
                        captcha_key)
                    self.logDebug(u"RECAPTCHA: %s : %s : %s" % (
                        captcha_key, post_dict['recaptcha_challenge_field'], post_dict['recaptcha_response_field']))

                download_url = self.getJsonResponse(get_dict, post_dict, 'link')
                if download_url:
                    if i:
                        self.correctCaptcha()
                    break
                elif i:
                    self.invalidCaptcha()

            else:
                self.fail("Invalid captcha")

        # Download
        self.download(download_url)

    def getJsonResponse(self, get_dict, post_dict, field):
        json_response = json_loads(self.load('https://filepost.com/files/get/', get=get_dict, post=post_dict))
        self.logDebug(json_response)

        if not 'js' in json_response:
            self.parseError('JSON %s 1' % field)

        # i changed js_answer to json_response['js'] since js_answer is nowhere set.
        # i don't know the JSON-HTTP specs in detail, but the previous author
        # accessed json_response['js']['error'] as well as js_answer['error'].
        # see the two lines commented out with  "# ~?".
        if 'error' in json_response['js']:
            if json_response['js']['error'] == 'download_delay':
                self.retry(wait_time=json_response['js']['params']['next_download'])
                # ~? self.retry(wait_time=js_answer['params']['next_download'])
            elif 'Wrong file password' in json_response['js']['error']:
                return None
            elif 'You entered a wrong CAPTCHA code' in json_response['js']['error']:
                return None
            elif 'CAPTCHA Code nicht korrekt' in json_response['js']['error']:
                return None
            elif 'CAPTCHA' in json_response['js']['error']:
                self.logDebug('error response is unknown, but mentions CAPTCHA -> return None')
                return None
            else:
                self.fail(json_response['js']['error'])
                # ~? self.fail(js_answer['error'])

        if not 'answer' in json_response['js'] or not field in json_response['js']['answer']:
            self.parseError('JSON %s 2' % field)

        return json_response['js']['answer'][field]


getInfo = create_getInfo(FilepostCom)
