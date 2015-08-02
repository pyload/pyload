# -*- coding: utf-8 -*-

import pycurl
import re

from module.common.json_layer import json_loads
from module.plugins.internal.Plugin import encode
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class UploadingCom(SimpleHoster):
    __name__    = "UploadingCom"
    __type__    = "hoster"
    __version__ = "0.43"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>\w+)'

    __description__ = """Uploading.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'id="file_title">(?P<N>.+?)</'
    SIZE_PATTERN = r'size tip_container">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r'(Page|file) not found'

    COOKIES = [("uploading.com", "lang", "1"),
               (".uploading.com", "language", "1"),
               (".uploading.com", "setlang", "en"),
               (".uploading.com", "_lang", "en")]


    def process(self, pyfile):
        if not "/get/" in pyfile.url:
            pyfile.url = pyfile.url.replace("/files", "/files/get")

        self.html = self.load(pyfile.url)
        self.get_fileInfo()

        if self.premium:
            self.handle_premium(pyfile)
        else:
            self.handle_free(pyfile)


    def handle_premium(self, pyfile):
        postData = {'action': 'get_link',
                    'code'  : self.info['pattern']['ID'],
                    'pass'  : 'undefined'}

        self.html = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.html)
        if url:
            self.link = url.group(1).replace("\\/", "/")

        raise Exception("Plugin defect")


    def handle_free(self, pyfile):
        m = re.search('<h2>((Daily )?Download Limit)</h2>', self.html)
        if m:
            pyfile.error = encode(m.group(1))
            self.log_warning(pyfile.error)
            self.retry(6, (6 * 60 if m.group(2) else 15) * 60, pyfile.error)

        ajax_url = "http://uploading.com/files/get/?ajax"
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = pyfile.url

        res = json_loads(self.load(ajax_url, post={'action': 'second_page', 'code': self.info['pattern']['ID']}))

        if 'answer' in res and 'wait_time' in res['answer']:
            wait_time = int(res['answer']['wait_time'])
            self.log_info(_("Waiting %d seconds") % wait_time)
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

        self.link = url


getInfo = create_getInfo(UploadingCom)
