# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class UploadingCom(SimpleHoster):
    __name__ = "UploadingCom"
    __type__ = "hoster"
    __version__ = "0.35"

    __pattern__ = r'http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>[\w\d]+)'

    __description__ = """Uploading.com hoster plugin"""
    __author_name__ = ("jeix", "mkaay", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'id="file_title">(?P<N>.+)</'
    FILE_SIZE_PATTERN = r'size tip_container">(?P<S>[\d.]+) (?P<U>\w+)<'
    OFFLINE_PATTERN = r'Page not found!'


    def process(self, pyfile):
        # set lang to english
        self.req.cj.setCookie(".uploading.com", "lang", "1")
        self.req.cj.setCookie(".uploading.com", "language", "1")
        self.req.cj.setCookie(".uploading.com", "setlang", "en")
        self.req.cj.setCookie(".uploading.com", "_lang", "en")

        if not "/get/" in pyfile.url:
            pyfile.url = pyfile.url.replace("/files", "/files/get")

        self.html = self.load(pyfile.url, decode=True)
        self.file_info = self.getFileInfo()

        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()

    def handlePremium(self):
        postData = {'action': 'get_link',
                    'code': self.file_info['ID'],
                    'pass': 'undefined'}

        self.html = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html)
        if url:
            url = url.group(1).replace("\\/", "/")
            self.download(url)

        raise Exception("Plugin defect.")

    def handleFree(self):
        m = re.search('<h2>((Daily )?Download Limit)</h2>', self.html)
        if m:
            self.pyfile.error = m.group(1)
            self.logWarning(self.pyfile.error)
            self.retry(max_tries=6, wait_time=6 * 60 * 60 if m.group(2) else 15 * 60, reason=self.pyfile.error)

        ajax_url = "http://uploading.com/files/get/?ajax"
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = self.pyfile.url

        response = json_loads(self.load(ajax_url, post={'action': 'second_page', 'code': self.file_info['ID']}))
        if 'answer' in response and 'wait_time' in response['answer']:
            wait_time = int(response['answer']['wait_time'])
            self.logInfo("%s: Waiting %d seconds." % (self.__name__, wait_time))
            self.wait(wait_time)
        else:
            self.parseError("AJAX/WAIT")

        response = json_loads(
            self.load(ajax_url, post={'action': 'get_link', 'code': self.file_info['ID'], 'pass': 'false'}))
        if 'answer' in response and 'link' in response['answer']:
            url = response['answer']['link']
        else:
            self.parseError("AJAX/URL")

        self.html = self.load(url)
        m = re.search(r'<form id="file_form" action="(.*?)"', self.html)
        if m:
            url = m.group(1)
        else:
            self.parseError("URL")

        self.download(url)

        check = self.checkDownload({"html": re.compile("\A<!DOCTYPE html PUBLIC")})
        if check == "html":
            self.logWarning("Redirected to a HTML page, wait 10 minutes and retry")
            self.wait(10 * 60, True)


getInfo = create_getInfo(UploadingCom)
