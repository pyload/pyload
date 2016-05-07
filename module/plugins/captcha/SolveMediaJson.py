# -*- coding: utf-8 -*-

import re

from module.plugins.internal.misc import json
from module.plugins.internal.Plugin import Fail
from module.plugins.internal.CaptchaService import CaptchaService


class SolveMediaJson(CaptchaService):
    __name__    = "SolveMediaJson"
    __type__    = "captcha"
    __version__ = "0.01"
    __status__  = "testing"

    __description__ = """SolveMedia captcha service plugin - JSON variant"""
    __license__     = "GPLv3"
    __authors__     = [("tbsn", "tbsnpy_github@gmx.de")]


    KEY_PATTERN = r'api\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'


    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m is not None:
            self.key = m.group(1).strip()
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_debug("Key pattern not found")
            return None


    def challenge(self, key=None, data=None):

        challengeRes = None

        key = key or self.retrieve_key(data)
        
        html = self.pyfile.plugin.load("http://api.solvemedia.com/papi/_challenge.js",
                                    get={'k': key})
                
        jsonResult = json.loads(html)
        if( 'ACChallengeResult' in jsonResult ):
            acChallengeResult = jsonResult['ACChallengeResult']
            if( 'chid' in acChallengeResult ):
                challengeRes =acChallengeResult['chid']
        
        if( None != challengeRes ):
            result = self.result("http://api.solvemedia.com/papi/media", challengeRes)
        
        return result, challengeRes
        

    def result(self, server, challenge):
        result = self.decrypt(server,
                              get={'c': challenge},
                              cookies=True,
                              input_type="gif")
        return result
