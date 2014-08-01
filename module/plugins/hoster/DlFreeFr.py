# -*- coding: utf-8 -*-

import pycurl
import re

from module.common.json_layer import json_loads
from module.network.Browser import Browser
from module.network.CookieJar import CookieJar
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns


class CustomBrowser(Browser):

    def __init__(self, bucket=None, options={}):
        Browser.__init__(self, bucket, options)

    def load(self, *args, **kwargs):
        post = kwargs.get("post")

        if post is None and len(args) > 2:
            post = args[2]

        if post:
            self.http.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.http.c.setopt(pycurl.POST, 1)
            self.http.c.setopt(pycurl.CUSTOMREQUEST, "POST")
        else:
            self.http.c.setopt(pycurl.FOLLOWLOCATION, 1)
            self.http.c.setopt(pycurl.POST, 0)
            self.http.c.setopt(pycurl.CUSTOMREQUEST, "GET")

        return Browser.load(self, *args, **kwargs)


class AdYouLike:
    """
    Class to support adyoulike captcha service
    """
    ADYOULIKE_INPUT_PATTERN = r'Adyoulike.create\((.*?)\);'
    ADYOULIKE_CALLBACK = r'Adyoulike.g._jsonp_5579316662423138'
    ADYOULIKE_CHALLENGE_PATTERN = ADYOULIKE_CALLBACK + r'\((.*?)\)'

    def __init__(self, plugin, engine="adyoulike"):
        self.plugin = plugin
        self.engine = engine

    def challenge(self, html):
        adyoulike_data_string = None
        m = re.search(self.ADYOULIKE_INPUT_PATTERN, html)
        if m:
            adyoulike_data_string = m.group(1)
        else:
            self.plugin.fail("Can't read AdYouLike input data")

        # {"adyoulike":{"key":"P~zQ~O0zV0WTiAzC-iw0navWQpCLoYEP"},
        # "all":{"element_id":"ayl_private_cap_92300","lang":"fr","env":"prod"}}
        ayl_data = json_loads(adyoulike_data_string)

        res = self.plugin.load(
            r'http://api-ayl.appspot.com/challenge?key=%(ayl_key)s&env=%(ayl_env)s&callback=%(callback)s' % {
            "ayl_key": ayl_data[self.engine]['key'], "ayl_env": ayl_data['all']['env'],
            "callback": self.ADYOULIKE_CALLBACK})

        m = re.search(self.ADYOULIKE_CHALLENGE_PATTERN, res)
        challenge_string = None
        if m:
            challenge_string = m.group(1)
        else:
            self.plugin.fail("Invalid AdYouLike challenge")
        challenge_data = json_loads(challenge_string)

        return ayl_data, challenge_data

    def result(self, ayl, challenge):
        """
        Adyoulike.g._jsonp_5579316662423138
        ({"translations":{"fr":{"instructions_visual":"Recopiez « Soonnight » ci-dessous :"}},
        "site_under":true,"clickable":true,"pixels":{"VIDEO_050":[],"DISPLAY":[],"VIDEO_000":[],"VIDEO_100":[],
        "VIDEO_025":[],"VIDEO_075":[]},"medium_type":"image/adyoulike",
        "iframes":{"big":"<iframe src=\"http://www.soonnight.com/campagn.html\" scrolling=\"no\"
        height=\"250\" width=\"300\" frameborder=\"0\"></iframe>"},"shares":{},"id":256,
        "token":"e6QuI4aRSnbIZJg02IsV6cp4JQ9~MjA1","formats":{"small":{"y":300,"x":0,"w":300,"h":60},
        "big":{"y":0,"x":0,"w":300,"h":250},"hover":{"y":440,"x":0,"w":300,"h":60}},
        "tid":"SqwuAdxT1EZoi4B5q0T63LN2AkiCJBg5"})
        """
        response = None
        try:
            instructions_visual = challenge['translations'][ayl['all']['lang']]['instructions_visual']
            m = re.search(u".*«(.*)».*", instructions_visual)
            if m:
                response = m.group(1).strip()
            else:
                self.plugin.fail("Can't parse instructions visual")
        except KeyError:
            self.plugin.fail("No instructions visual")

        #TODO: Supports captcha

        if not response:
            self.plugin.fail("AdYouLike result failed")

        return {"_ayl_captcha_engine": self.engine,
                "_ayl_env": ayl['all']['env'],
                "_ayl_tid": challenge['tid'],
                "_ayl_token_challenge": challenge['token'],
                "_ayl_response": response}


class DlFreeFr(SimpleHoster):
    __name__ = "DlFreeFr"
    __type__ = "hoster"
    __version__ = "0.25"

    __pattern__ = r'http://(?:www\.)?dl\.free\.fr/([a-zA-Z0-9]+|getfile\.pl\?file=/[a-zA-Z0-9]+)'

    __description__ = """Dl.free.fr hoster plugin"""
    __author_name__ = ("the-razer", "zoidberg", "Toilal")
    __author_mail__ = ("daniel_ AT gmx DOT net", "zoidberg@mujmail.cz", "toilal.dev@gmail.com")

    FILE_NAME_PATTERN = r'Fichier:</td>\s*<td[^>]*>(?P<N>[^>]*)</td>'
    FILE_SIZE_PATTERN = r'Taille:</td>\s*<td[^>]*>(?P<S>[\d.]+[KMG])o'
    OFFLINE_PATTERN = r"Erreur 404 - Document non trouv|Fichier inexistant|Le fichier demand&eacute; n'a pas &eacute;t&eacute; trouv&eacute;"


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.limitDL = 5
        self.chunkLimit = 1

    def init(self):
        factory = self.core.requestFactory
        self.req = CustomBrowser(factory.bucket, factory.getOptions())

    def process(self, pyfile):
        self.req.setCookieJar(None)

        pyfile.url = replace_patterns(pyfile.url, self.FILE_URL_REPLACEMENTS)
        valid_url = pyfile.url
        headers = self.load(valid_url, just_header=True)

        self.html = None
        if headers.get('code') == 302:
            valid_url = headers.get('location')
            headers = self.load(valid_url, just_header=True)

        if headers.get('code') == 200:
            content_type = headers.get('content-type')
            if content_type and content_type.startswith("text/html"):
                # Undirect acces to requested file, with a web page providing it (captcha)
                self.html = self.load(valid_url)
                self.handleFree()
            else:
                # Direct access to requested file for users using free.fr as Internet Service Provider.
                self.download(valid_url, disposition=True)
        elif headers.get('code') == 404:
            self.offline()
        else:
            self.fail("Invalid return code: " + str(headers.get('code')))

    def handleFree(self):
        action, inputs = self.parseHtmlForm('action="getfile.pl"')

        adyoulike = AdYouLike(self)
        ayl, challenge = adyoulike.challenge(self.html)
        result = adyoulike.result(ayl, challenge)
        inputs.update(result)

        self.load("http://dl.free.fr/getfile.pl", post=inputs)
        headers = self.getLastHeaders()
        if headers.get("code") == 302 and "set-cookie" in headers and "location" in headers:
            m = re.search("(.*?)=(.*?); path=(.*?); domain=(.*?)", headers.get("set-cookie"))
            cj = CookieJar(__name__)
            if m:
                cj.setCookie(m.group(4), m.group(1), m.group(2), m.group(3))
            else:
                self.fail("Cookie error")
            location = headers.get("location")
            self.req.setCookieJar(cj)
            self.download(location, disposition=True)
        else:
            self.fail("Invalid response")

    def getLastHeaders(self):
        #parse header
        header = {"code": self.req.code}
        for line in self.req.http.header.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, none, value = line.partition(":")
            key = key.lower().strip()
            value = value.strip()

            if key in header:
                if type(header[key]) == list:
                    header[key].append(value)
                else:
                    header[key] = [header[key], value]
            else:
                header[key] = value
        return header


getInfo = create_getInfo(DlFreeFr)
