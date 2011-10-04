#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string

from types import MethodType

from module.plugins.Hoster import Hoster
from module.plugins.Plugin import chunks

from module.network.RequestFactory import getURL
from module.common.json_layer import json_loads


def getInfo(urls):
    for chunk in chunks(urls, 20):
        result = []
        ids = dict()
        for url in chunk:
            id = getId(url)
            if id:
                ids[id] = url
            else:
                result.append((None, 0, 1, url))

        if len(ids) > 0:
            check_url = "http://api.wupload.com/link?method=getInfo&format=json&ids=" + ",".join(ids.keys())
            response = json_loads(getURL(check_url).decode("utf8", "ignore"))
            for item in response["FSApi_Link"]["getInfo"]["response"]["links"]:
                if item["status"] != "AVAILABLE":
                    result.append((None, 0, 1, ids[str(item["id"])]))
                else:
                    result.append((item["filename"], item["size"], 2, ids[str(item["id"])]))
        yield result


def getId(url):
    match = re.search(WuploadCom.FILE_ID_PATTERN, url)
    if match:
        return string.replace(match.group("id"), "/", "-")
    else:
        return None


class WuploadCom(Hoster):
    __name__ = "WuploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?wupload\..*?/file/(([a-z][0-9]+/)?[0-9]+)(/.*)?"
    __version__ = "0.1"
    __description__ = """Wupload com"""
    __author_name__ = ("jeix", "paulking")
    __author_mail__ = ("jeix@hasnomail.de", "")

    API_ADDRESS = "http://api.wupload.com"
    URL_DOMAIN_PATTERN = r'(?P<prefix>.*?)(?P<domain>.wupload\..+?)(?P<suffix>/.*)'
    FILE_ID_PATTERN = r'/file/(?P<id>([a-z][0-9]+/)?[0-9]+)(/.*)?'
    FILE_LINK_PATTERN = r'<p><a href="(http://.+?\.wupload\..+?)"><span>Download Now'
    WAIT_TIME_PATTERN = r'countDownDelay = (?P<wait>\d+)'
    WAIT_TM_PATTERN = r"name='tm' value='(.*?)' />"
    WAIT_TM_HASH_PATTERN = r"name='tm_hash' value='(.*?)' />"
    CAPTCHA_TYPE1_PATTERN = r'Recaptcha.create\("(.*?)",'
    CAPTCHA_TYPE2_PATTERN = r'id="recaptcha_image"><img style="display: block;" src="(.+)image?c=(.+?)"'

    def init(self):
        #this plugin shares most things with filesonic, always keep in mind when editing it

        module = self.core.pluginManager.getPlugin("FilesonicCom")
        fs = getattr(module, "FilesonicCom")

        self.newInit = MethodType(fs.__dict__["init"], self, WuploadCom)

        methods = ["process", "checkFile", "downloadPremium", "downloadFree", "doWait", "handleErrors"]
        #methods to bind from fs

        for m in methods:
            setattr(self, m, MethodType(fs.__dict__[m], self, WuploadCom))

        self.newInit()


    def getDomain(self):
        result = json_loads(
            self.load(self.API_ADDRESS + "/utility?method=getWuploadDomainForCurrentIp&format=json", decode=True))
        self.log.debug("%s: response to get domain %s" % (self.__name__, result))
        return result["FSApi_Utility"]["getWuploadDomainForCurrentIp"]["response"]