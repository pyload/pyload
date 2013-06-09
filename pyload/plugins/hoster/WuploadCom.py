#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string
from urllib import unquote

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
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
                    result.append((unquote(item["filename"]), item["size"], 2, ids[str(item["id"])]))
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
    __version__ = "0.20"
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
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
        if not self.premium:
            self.chunkLimit = 1
            self.multiDL = False

    def process(self, pyfile):
        self.pyfile = pyfile

        self.pyfile.url = self.checkFile(self.pyfile.url)

        if self.premium:
            self.downloadPremium()
        else:
            self.downloadFree()

    def checkFile(self, url):
        id = getId(url)
        self.logDebug("file id is %s" % id)
        if id:
            # Use the api to check the current status of the file and fixup data
            check_url = self.API_ADDRESS + "/link?method=getInfo&format=json&ids=%s" % id
            result = json_loads(self.load(check_url, decode=True))
            item = result["FSApi_Link"]["getInfo"]["response"]["links"][0]
            self.logDebug("api check returns %s" % item)

            if item["status"] != "AVAILABLE":
                self.offline()
            if item["is_password_protected"] != 0:
                self.fail("This file is password protected")

            # ignored this check due to false api information
            #if item["is_premium_only"] != 0 and not self.premium:
            #    self.fail("need premium account for file")

            self.pyfile.name = unquote(item["filename"])

            # Fix the url and resolve the domain to the correct regional variation
            url = item["url"]
            urlparts = re.search(self.URL_DOMAIN_PATTERN, url)
            if urlparts:
                url = urlparts.group("prefix") + self.getDomain() + urlparts.group("suffix")
                self.logDebug("localised url is %s" % url)
            return url
        else:
            self.fail("Invalid URL")

    def getDomain(self):
        result = json_loads(
            self.load(self.API_ADDRESS + "/utility?method=getWuploadDomainForCurrentIp&format=json", decode=True))
        self.log.debug("%s: response to get domain %s" % (self.__name__, result))
        return result["FSApi_Utility"]["getWuploadDomainForCurrentIp"]["response"]

    def downloadPremium(self):
        self.logDebug("Premium download")

        api = self.API_ADDRESS + "/link?method=getDownloadLink&u=%%s&p=%%s&ids=%s" % getId(self.pyfile.url)

        result = json_loads(self.load(api % (self.user, self.account.getAccountData(self.user)["password"])))
        links = result["FSApi_Link"]["getDownloadLink"]["response"]["links"]

        #wupload seems to return list and no dicts
        if type(links) == dict:
            info = links.values()[0]
        else:
            info = links[0]

        if "status" in info and info["status"] == "NOT_AVAILABLE":
            self.tempOffline()

        self.download(info["url"])

    def downloadFree(self):
        self.logDebug("Free download")
        # Get initial page
        self.html = self.load(self.pyfile.url)
        url = self.pyfile.url + "?start=1"
        self.html = self.load(url)
        self.handleErrors()

        finalUrl = re.search(self.FILE_LINK_PATTERN, self.html)

        if not finalUrl:
            self.doWait(url)

            chall = re.search(self.CAPTCHA_TYPE1_PATTERN, self.html)
            chall2 = re.search(self.CAPTCHA_TYPE2_PATTERN, self.html)
            if chall or chall2:
                for i in range(5):
                    re_captcha = ReCaptcha(self)
                    if chall:
                        self.logDebug("Captcha type1")
                        challenge, result = re_captcha.challenge(chall.group(1))
                    else:
                        self.logDebug("Captcha type2")
                        server = chall2.group(1)
                        challenge = chall2.group(2)
                        result = re_captcha.result(server, challenge)

                    postData = {"recaptcha_challenge_field": challenge,
                                "recaptcha_response_field": result}

                    self.html = self.load(url, post=postData)
                    self.handleErrors()
                    chall = re.search(self.CAPTCHA_TYPE1_PATTERN, self.html)
                    chall2 = re.search(self.CAPTCHA_TYPE2_PATTERN, self.html)

                    if chall or chall2:
                        self.invalidCaptcha()
                    else:
                        self.correctCaptcha()
                        break

            finalUrl = re.search(self.FILE_LINK_PATTERN, self.html)

        if not finalUrl:
            self.fail("Couldn't find free download link")

        self.logDebug("got download url %s" % finalUrl.group(1))
        self.download(finalUrl.group(1))

    def doWait(self, url):
        # If the current page requires us to wait then wait and move to the next page as required

        # There maybe more than one wait period. The extended wait if download limits have been exceeded (in which case we try reconnect)
        # and the short wait before every download. Visually these are the same, the difference is that one includes a code to allow
        # progress to the next page

        waitSearch = re.search(self.WAIT_TIME_PATTERN, self.html)
        while waitSearch:
            wait = int(waitSearch.group("wait"))
            if wait > 300:
                self.wantReconnect = True

            self.setWait(wait)
            self.logDebug("Waiting %d seconds." % wait)
            self.wait()

            tm = re.search(self.WAIT_TM_PATTERN, self.html)
            tm_hash = re.search(self.WAIT_TM_HASH_PATTERN, self.html)

            if tm and tm_hash:
                tm = tm.group(1)
                tm_hash = tm_hash.group(1)
                self.html = self.load(url, post={"tm": tm, "tm_hash": tm_hash})
                self.handleErrors()
                break
            else:
                self.html = self.load(url)
                self.handleErrors()
                waitSearch = re.search(self.WAIT_TIME_PATTERN, self.html)

    def handleErrors(self):
        if "This file is available for premium users only." in self.html:
            self.fail("need premium account for file")

        if "The file that you're trying to download is larger than" in self.html:
            self.fail("need premium account for file")

        if "Free users may only download 1 file at a time" in self.html:
            self.fail("only 1 file at a time for free users")

        if "Free user can not download files" in self.html:
            self.fail("need premium account for file")

        if "Download session in progress" in self.html:
            self.fail("already downloading")

        if "This file is password protected" in self.html:
            self.fail("This file is password protected")

        if "An Error Occurred" in self.html:
            self.fail("A server error occured.")

        if "This file was deleted" in self.html:
            self.offline()
