# -*- coding: utf-8 -*-

import re

from ..internal.CaptchaService import CaptchaService
from ..internal.misc import json


class AdYouLike(CaptchaService):
    __name__ = "AdYouLike"
    __type__ = "captcha"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """AdYouLike captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    AYL_PATTERN = r'Adyoulike\.create\s*\((.+?)\)'
    CALLBACK_PATTERN = r'(Adyoulike\.g\._jsonp_\d+)'

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.AYL_PATTERN, html)
        n = re.search(self.CALLBACK_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())
            self.log_debug("Ayl: %s | Callback: %s" % self.key)
            return self.key   #: Key is the tuple(ayl, callback)
        else:
            self.log_debug("Ayl or callback pattern not found")
            return None

    def challenge(self, key=None, data=None):
        ayl, callback = key or self.retrieve_key(data)

        #: {'adyoulike':{'key':"P~zQ~O0zV0WTiAzC-iw0navWQpCLoYEP"},
        #: 'all':{'element_id':"ayl_private_cap_92300",'lang':"fr",'env':"prod"}}
        ayl = json.loads(ayl)

        html = self.pyfile.plugin.load("http://api-ayl.appspot.com/challenge",
                                       get={'key': ayl['adyoulike']['key'],
                                            'env': ayl['all']['env'],
                                            'callback': callback})
        try:
            challenge = json.loads(
                re.search(
                    callback +
                    r'\s*\((.+?)\)',
                    html).group(1))

        except AttributeError:
            self.fail(_("AdYouLike challenge pattern not found"))

        self.log_debug("Challenge: %s" % challenge)

        return self.result(ayl, challenge), challenge

    def result(self, server, challenge):
        #: Adyoulike.g._jsonp_5579316662423138
        #: ({'translations':{'fr':{'instructions_visual':"Recopiez « Soonnight » ci-dessous :"}},
        #: 'site_under':true,'clickable':true,'pixels':{'VIDEO_050':[],'DISPLAY':[],'VIDEO_000':[],'VIDEO_100':[],
        #: 'VIDEO_025':[],'VIDEO_075':[]},'medium_type':"image/adyoulike",
        #: 'iframes':{'big':"<iframe src=\"http://www.soonnight.com/campagn.html\" scrolling=\"no\"
        #: height=\"250\" width=\"300\" frameborder=\"0\"></iframe>"},'shares':{},'id':256,
        #: 'token':"e6QuI4aRSnbIZJg02IsV6cp4JQ9~MjA1",'formats':{'small':{'y':300,'x':0,'w':300,'h':60},
        #: 'big':{'y':0,'x':0,'w':300,'h':250},'hover':{'y':440,'x':0,'w':300,'h':60}},
        #: 'tid':"SqwuAdxT1EZoi4B5q0T63LN2AkiCJBg5"})

        if isinstance(server, basestring):
            server = json.loads(server)

        if isinstance(challenge, basestring):
            challenge = json.loads(challenge)

        try:
            instructions_visual = challenge['translations'][
                server['all']['lang']]['instructions_visual']
            response = re.search(
                u'«(.+?)»', instructions_visual).group(1).strip()

        except AttributeError:
            self.fail(_("AdYouLike result not found"))

        result = {'_ayl_captcha_engine': "adyoulike",
                  '_ayl_env': server['all']['env'],
                  '_ayl_tid': challenge['tid'],
                  '_ayl_token_challenge': challenge['token'],
                  '_ayl_response': response}

        return result
