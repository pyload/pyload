# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class UploadingCom(SimpleHoster):
    __name__    = "UploadingCom"
    __type__    = "hoster"
    __version__ = "0.40"

    __pattern__ = r'http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>\w+)'

    __description__ = """Uploading.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'id="file_title">(?P<N>.+)</'
    SIZE_PATTERN = r'size tip_container">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r'(Page|file) not found'

    COOKIES = [("uploading.com", "lang", "1"),
               (".uploading.com", "language", "1"),
               (".uploading.com", "setlang", "en"),
               (".uploading.com", "_lang", "en")]


    def process(self, pyfile):
        if not "/get/" in pyfile.url:
            pyfile.url = pyfile.url.replace("/files", "/files/get")

        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()

        if self.premium:
            self.handlePremium(pyfile)
        else:
            self.handleFree(pyfile)


    def handlePremium(self, pyfile):
        postData = {'action': 'get_link',
                    'code'  : self.info['pattern']['ID'],
                    'pass'  : 'undefined'}

        self.html = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html)
        if url:
            url = url.group(1).replace("\\/", "/")
            self.download(url)

        raise Exception("Plugin defect")


    def handleFree(self, pyfile):
        m = re.search('<h2>((Daily )?Download Limit)</h2>', self.html)
        if m:
            pyfile.error = m.group(1)
            self.logWarning(pyfile.error)
            self.retry(6, (6 * 60 if m.group(2) else 15) * 60, pyfile.error)

        ajax_url = "http://uploading.com/files/get/?ajax"
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = pyfile.url

        res = json_loads(self.load(ajax_url, post={'action': 'second_page', 'code': self.info['pattern']['ID']}))

        if 'answer' in res and 'wait_time' in res['answer']:
            wait_time = int(res['answer']['wait_time'])
            self.logInfo(_("Waiting %d seconds") % wait_time)
            self.wait(wait_time)
        else:
            self.error(_("No AJAX/WAIT"))

        res = json_loads(self.load(ajax_url, post={'action': 'get_link', 'code': self.info['pattern']['ID'], 'pass': 'false'}))

        if 'answer' in res and 'link' in res['answer']:
            url = res['answer']['link']
        else:
            self.error(_("No AJAX/URL"))

        self.html = self.load(url)
        m = re.search(r'<form id="file_form" action="(.*?)"', self.html)
        if m:
            url = m.group(1)
        else:
            self.error(_("No URL"))

        self.download(url)


getInfo = create_getInfo(UploadingCom)
